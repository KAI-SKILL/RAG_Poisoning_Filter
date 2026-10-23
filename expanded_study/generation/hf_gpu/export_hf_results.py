#!/usr/bin/env python3
"""Export a stopped HF run as closed SQLite files and an explicit result ZIP."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,sqlite3,tempfile,zipfile

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def db_state(path):
    if not path.exists():return {'responses':0,'config_sha256':None}
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);db.row_factory=sqlite3.Row
    try:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Response database integrity failed')
        metadata=dict(db.execute('SELECT key,value FROM metadata'));config=json.loads(metadata['config'])
        canonical=json.dumps(config,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
        if hashlib.sha256(canonical.encode()).hexdigest()!=metadata['config_sha256']:raise ValueError('Stored configuration hash mismatch')
        snapshot=hashlib.sha256();count=0
        for row in db.execute('SELECT * FROM responses ORDER BY prompt_sha256'):
            record=dict(row)
            if record.get('config_sha256')!=metadata['config_sha256']:raise ValueError('Response/configuration mismatch')
            snapshot.update((json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode());count+=1
        return {'responses':count,'config_sha256':metadata['config_sha256'],'config':config,'response_snapshot_sha256':snapshot.hexdigest()}
    finally:db.close()

def export(source,destination,complete_validator=None):
    source=source.resolve();destination=destination.resolve()
    if not source.is_dir():raise ValueError('Source output directory missing')
    if source==destination or source in destination.parents or destination in source.parents:raise ValueError('Output export directories must be separate')
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=destination.name+'-export-',dir=destination.parent))
    previous=None
    try:
        for p in sorted(source.rglob('*')):
            rel=p.relative_to(source)
            if not p.is_file() or any(x.startswith('.') or x=='__pycache__' for x in rel.parts) or p.name.endswith(('-wal','-shm','-journal','.partial','.pyc')):continue
            out=stage/rel;out.parent.mkdir(parents=True,exist_ok=True)
            if p.name=='generation_responses.sqlite':
                incoming=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True);closed=sqlite3.connect(out)
                try:
                    incoming.backup(closed);closed.commit()
                    assert closed.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                    closed.execute('PRAGMA journal_mode=DELETE');closed.commit()
                finally:closed.close();incoming.close()
            else:
                if p.suffix=='.sqlite':
                    wal=p.with_name(p.name+'-wal')
                    if wal.exists() and wal.stat().st_size:raise ValueError('Immutable input still has a live WAL; stop the writer before export')
                # Native input bytes are fingerprinted by the runner. Preserve them.
                shutil.copy2(p,out)
        state=db_state(stage/'generation_responses.sqlite')
        if destination.exists():
            old=db_state(destination/'generation_responses.sqlite')
            if old['responses'] and (state['config_sha256']!=old['config_sha256'] or state['responses']<old['responses']):raise ValueError('Refusing to replace a different configuration or a more advanced saved checkpoint')
            if old['responses']:
                db=sqlite3.connect((stage/'generation_responses.sqlite').resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
                db.execute('ATTACH DATABASE ? AS old',(str(destination/'generation_responses.sqlite'),))
                missing=db.execute('SELECT prompt_sha256,response,raw_json FROM old.responses EXCEPT SELECT prompt_sha256,response,raw_json FROM main.responses').fetchone();db.close()
                if missing is not None:raise ValueError('Existing saved responses changed or disappeared')
        m=json.loads((stage/'run_manifest.json').read_text())if(stage/'run_manifest.json').exists()else{}
        expected=None;request_rows=None;coverage_ok=False
        if (stage/'native_inputs.sqlite').exists():
            db=sqlite3.connect((stage/'native_inputs.sqlite').resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
            expected=db.execute('SELECT COUNT(*) FROM prompts').fetchone()[0]
            request_rows=db.execute('SELECT COUNT(*) FROM requests').fetchone()[0];db.close()
            if (stage/'generation_responses.sqlite').exists():
                db=sqlite3.connect((stage/'generation_responses.sqlite').resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
                db.execute('ATTACH DATABASE ? AS native',((stage/'native_inputs.sqlite').resolve().as_uri()+'?mode=ro&immutable=1',))
                missing=db.execute('SELECT prompt_sha256 FROM native.prompts EXCEPT SELECT prompt_sha256 FROM responses').fetchone()
                extra=db.execute('SELECT prompt_sha256 FROM responses EXCEPT SELECT prompt_sha256 FROM native.prompts').fetchone();db.close()
                coverage_ok=missing is None and extra is None
        scoring_ok=False;scoring_issues=[]
        score_path=stage/'scoring/scoring_manifest.json';protocol_path=stage/'scoring_protocol.json'
        if score_path.exists() and protocol_path.exists():
            score=json.loads(score_path.read_text());protocol=json.loads(protocol_path.read_text())
            expected_fields={'status':'COMPLETE_GENERATION_SCORING','response_config_sha256':state['config_sha256'],'response_snapshot_sha256':state['response_snapshot_sha256'],'input_sqlite_sha256':sha(stage/'native_inputs.sqlite'),'native_protocol_sha256':sha(protocol_path),'metric_source_sha256':protocol['scorer_sha256'],'requested_rows':request_rows,'scored_request_rows':request_rows,'missing_unique_prompts':0,'expected_unique_prompts':expected,'actual_unique_response_records':state['responses']}
            for key,value in expected_fields.items():
                if score.get(key)!=value:scoring_issues.append('Scoring identity mismatch: '+key)
            try:
                if json.loads(score['response_config_json'])!=state['config']:scoring_issues.append('Scoring configuration JSON mismatch')
            except (KeyError,ValueError,TypeError):scoring_issues.append('Missing or malformed scoring configuration JSON')
            hashes=score.get('closed_output_hashes')
            if not hashes:scoring_issues.append('No closed scoring output fingerprints')
            else:
                for name,digest in hashes.items():
                    p=(stage/'scoring'/name).resolve()
                    if (stage/'scoring').resolve()not in p.parents or not p.is_file() or sha(p)!=digest:scoring_issues.append('Scoring output mismatch: '+name)
            scoring_ok=not scoring_issues
        complete=bool(expected and state['responses']==expected and coverage_ok and m.get('status')=='COMPLETE' and m.get('config_sha256')==state['config_sha256'] and scoring_ok)
        additional_validation=None
        if complete_validator is not None:
            try:
                additional_validation=complete_validator(stage)
                if not isinstance(additional_validation,dict) or additional_validation.get('status')!='COMPLETE':
                    complete=False
            except Exception as error:
                complete=False
                additional_validation={'status':'INCOMPLETE_OR_INVALID_RESULT','issues':[type(error).__name__+': '+str(error)]}
        receipt={'status':'COMPLETE_GENERATION_AND_SCORING'if complete else'INCOMPLETE_CHECKPOINT','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_unique_responses':state['responses'],'expected_unique_prompts':expected,'config_sha256':state['config_sha256'],'source_runner_status':m.get('status'),'scoring_integrity_issues':scoring_issues,'full_asr_ready':complete,'exporter_model_calls':0,'scope':'Only a COMPLETE archive with full response coverage and fingerprint-verified formal scoring is a finished experiment.'}
        if complete_validator is not None:receipt['additional_scope_validation']=additional_validation
        (stage/'export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        files=[p for p in sorted(stage.rglob('*'))if p.is_file()]
        (stage/'export_files.json').write_text(json.dumps([{'path':p.relative_to(stage).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}for p in files],indent=2)+'\n')
        suffix='COMPLETE_Results'if complete else'INCOMPLETE_Checkpoint'
        archive=destination.parent/(destination.name+'_'+suffix+'.zip');temporary=archive.with_suffix('.zip.partial')
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True)as z:
            for p in sorted(stage.rglob('*')):
                if p.is_file():z.write(p,arcname=(Path(destination.name)/p.relative_to(stage)).as_posix())
        with zipfile.ZipFile(temporary)as z:
            if z.testzip()is not None:raise OSError('Result ZIP CRC validation failed')
        if destination.exists():
            previous=destination.with_name(destination.name+'-previous-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
            destination.rename(previous)
        stage.rename(destination);os.replace(temporary,archive)
        if previous is not None:shutil.rmtree(previous)
        return {**receipt,'directory':str(destination),'archive':str(archive),'archive_bytes':archive.stat().st_size}
    finally:
        if stage.exists():shutil.rmtree(stage)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
    print(json.dumps(export(a.source,a.destination),indent=2))

if __name__=='__main__':main()
