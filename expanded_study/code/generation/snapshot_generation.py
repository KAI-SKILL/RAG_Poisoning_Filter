"""Save a consistent, explicitly partial checkpoint while generation continues."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,sqlite3

def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--inputs',type=Path,required=True);p.add_argument('--run',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise SystemExit('Refusing snapshot overwrite; choose a new output directory')
 a.output.mkdir(parents=True);target=a.output/'generation_responses.sqlite'
 source=sqlite3.connect('file:'+str((a.run/'generation_responses.sqlite').resolve())+'?mode=ro',uri=True)
 backup=sqlite3.connect(target);source.backup(backup);source.close()
 assert backup.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 metadata=dict(backup.execute('SELECT key,value FROM metadata'));config=json.loads(metadata['config'])
 assert hashlib.sha256(json.dumps(config,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==metadata['config_sha256']
 count=backup.execute('SELECT count(*) FROM responses').fetchone()[0]
 backup.row_factory=sqlite3.Row
 with (a.output/'raw_unique_responses.jsonl').open('w')as f:
  for row in backup.execute('SELECT * FROM responses ORDER BY batch_id,prompt_sha256'):
   f.write(json.dumps(dict(row),ensure_ascii=False,allow_nan=False)+'\n')
  f.flush();os.fsync(f.fileno())
 attempts=backup.execute('SELECT status,count(*) AS n FROM attempts GROUP BY status').fetchall()
 backup.execute('PRAGMA query_only=ON');backup.execute('ATTACH DATABASE ? AS frozen',(str(a.inputs.resolve()),))
 expected=backup.execute('SELECT count(*) FROM frozen.prompts').fetchone()[0]
 requested=backup.execute('SELECT count(*) FROM frozen.requests').fetchone()[0]
 extra=backup.execute('SELECT count(*) FROM responses r LEFT JOIN frozen.prompts p ON r.prompt_sha256=p.prompt_sha256 WHERE p.prompt_sha256 IS NULL').fetchone()[0]
 coverage=backup.execute('SELECT count(*) AS rows,count(DISTINCT q.question_id) AS questions,count(DISTINCT q.article_id) AS articles FROM frozen.requests q JOIN responses r ON q.prompt_sha256=r.prompt_sha256').fetchone()
 assert extra==0
 backup.close()
 receipt={'status':'COMPLETE_RESPONSE_SNAPSHOT'if count==expected else 'INCOMPLETE_RESPONSE_SNAPSHOT_NOT_FULL_ASR','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'unique_committed_responses':count,'expected_unique_prompts':expected,'missing_unique_prompts':expected-count,'full_grid_request_rows':requested,'request_rows_with_committed_response':coverage['rows'],'questions_with_any_committed_response':coverage['questions'],'articles_with_any_committed_response':coverage['articles'],'attempt_status_counts':{r['status']:r['n']for r in attempts},'config_sha256':metadata['config_sha256'],'input_sqlite_sha256_from_execution':config['input_sqlite_sha256'],'response_database_sha256':digest(target),'raw_response_jsonl_sha256':digest(a.output/'raw_unique_responses.jsonl'),'snapshot_producer_sha256':digest(Path(__file__)),'source_run_is_modified':False,'model_calls_by_snapshotter':0,'scope':'SQLite online backup of committed records, not final scoring. Missing responses are unexecuted/uncommitted, never failed attacks; in-flight attempts remain explicitly unresolved.'}
 (a.output/'snapshot_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 (a.output/'execution_config.json').write_text(json.dumps(config,indent=2)+'\n')
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
