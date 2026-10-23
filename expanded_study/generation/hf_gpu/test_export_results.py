"""Offline fixtures for durable result export; no model imports or GPU calls."""
from pathlib import Path
import importlib.util,json,sqlite3,tempfile,zipfile

module_path=Path(__file__).with_name('export_hf_results.py')
spec=importlib.util.spec_from_file_location('group9_export_fixture',module_path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def main():
    checks=[]
    with tempfile.TemporaryDirectory(prefix='group9-hf-export-test-')as folder:
        root=Path(folder);source=root/'local';source.mkdir();dest=root/'shared'/'qwen3_8b'
        p=sqlite3.connect(source/'native_inputs.sqlite');p.execute('CREATE TABLE prompts(prompt_sha256 TEXT PRIMARY KEY)');p.executemany('INSERT INTO prompts VALUES(?)',[('a',),('b',)]);p.execute('CREATE TABLE requests(prompt_sha256 TEXT)');p.executemany('INSERT INTO requests VALUES(?)',[('a',),('b',)]);p.commit();p.close()
        native_hash=module.sha(source/'native_inputs.sqlite')
        db=sqlite3.connect(source/'generation_responses.sqlite');db.execute('PRAGMA journal_mode=WAL')
        config=json.dumps({'fixture':True},sort_keys=True,separators=(',',':'));config_hash=module.hashlib.sha256(config.encode()).hexdigest()
        db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)');db.executemany('INSERT INTO metadata VALUES(?,?)',[('config_sha256',config_hash),('config',config)])
        db.execute('CREATE TABLE responses(prompt_sha256 TEXT PRIMARY KEY,response TEXT,raw_json TEXT,config_sha256 TEXT)');db.execute('INSERT INTO responses VALUES(?,?,?,?)',('a','fixture-a','{}',config_hash));db.commit()
        (source/'run_manifest.json').write_text(json.dumps({'status':'PAUSED_BY_CONTROL_FILE','config_sha256':config_hash}))
        a=module.export(source,dest)
        assert a['status']=='INCOMPLETE_CHECKPOINT'and a['actual_unique_responses']==1
        assert module.sha(dest/'native_inputs.sqlite')==native_hash
        assert not list(dest.rglob('*-wal'))and not list(dest.rglob('*-shm'))
        assert module.db_state(dest/'generation_responses.sqlite')['responses']==1
        checks.append('incomplete_live_wal_backup_keeps_input_bytes_and_closes_database')
        db.execute('INSERT INTO responses VALUES(?,?,?,?)',('b','fixture-b','{}',config_hash));db.commit()
        (source/'run_manifest.json').write_text(json.dumps({'status':'COMPLETE','config_sha256':config_hash}))
        b=module.export(source,dest)
        assert b['status']=='INCOMPLETE_CHECKPOINT','Coverage without scoring must remain incomplete'
        checks.append('full_response_coverage_without_formal_scoring_not_complete')
        (source/'scoring').mkdir();(source/'scoring/summary.json').write_text('{"fixture":true}')
        (source/'scoring_protocol.json').write_text('{"scorer_sha256":"fixture-metric"}')
        score={'status':'COMPLETE_GENERATION_SCORING','response_config_sha256':config_hash,'response_config_json':config,'response_snapshot_sha256':module.db_state(dest/'generation_responses.sqlite')['response_snapshot_sha256'],'input_sqlite_sha256':native_hash,'native_protocol_sha256':module.sha(source/'scoring_protocol.json'),'metric_source_sha256':'fixture-metric','closed_output_hashes':{'summary.json':module.sha(source/'scoring/summary.json')},'requested_rows':2,'scored_request_rows':2,'expected_unique_prompts':2,'actual_unique_response_records':2,'missing_unique_prompts':0}
        (source/'scoring/scoring_manifest.json').write_text(json.dumps(score))
        c=module.export(source,dest)
        assert c['status']=='COMPLETE_GENERATION_AND_SCORING'and c['full_asr_ready']
        with zipfile.ZipFile(c['archive'])as z:assert z.testzip()is None
        checks.append('full_coverage_with_formal_scoring_exports_complete_zip')
        db.execute("UPDATE responses SET prompt_sha256='unexpected'WHERE prompt_sha256='b'");db.commit()
        wrong_keys=module.export(source,root/'shared/wrong-key-fixture')
        assert wrong_keys['status']=='INCOMPLETE_CHECKPOINT'
        db.execute("UPDATE responses SET prompt_sha256='b'WHERE prompt_sha256='unexpected'");db.commit()
        checks.append('same_response_count_with_wrong_prompt_key_not_complete')
        db.execute("UPDATE responses SET response='changed-content'WHERE prompt_sha256='b'");db.commit()
        changed=module.export(source,root/'shared/changed-content-fixture')
        assert changed['status']=='INCOMPLETE_CHECKPOINT'and any('response_snapshot' in issue for issue in changed['scoring_integrity_issues'])
        db.execute("UPDATE responses SET response='fixture-b'WHERE prompt_sha256='b'");db.commit()
        checks.append('same_keys_count_configuration_with_changed_response_not_complete')
        (source/'scoring/summary.json').write_text('{"fixture":"changed"}')
        broken=module.export(source,dest)
        assert broken['status']=='INCOMPLETE_CHECKPOINT'and broken['scoring_integrity_issues']
        checks.append('changed_scoring_output_cannot_export_as_complete')
        db.execute("UPDATE metadata SET value='different-config'WHERE key='config_sha256'");db.commit()
        try:module.export(source,dest)
        except ValueError:pass
        else:raise AssertionError('Different configuration overwrote saved results')
        assert module.db_state(dest/'generation_responses.sqlite')['config_sha256']==config_hash
        checks.append('changed_configuration_rejected_without_replacing_saved_results')
        db.close()
    result={'status':'PASS','tests':checks,'real_model_calls':0,'gpu_calls':0}
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
