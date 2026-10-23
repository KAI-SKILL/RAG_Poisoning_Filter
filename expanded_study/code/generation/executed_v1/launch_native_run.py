"""Own the local server and generation client in one process namespace."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time,urllib.request

def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,required=True);p.add_argument('--server',type=Path,required=True)
 p.add_argument('--model',type=Path,required=True);p.add_argument('--build-manifest',type=Path,required=True)
 p.add_argument('--batch-size',type=int,default=8);p.add_argument('--threads',type=int,default=8)
 p.add_argument('--port',type=int,default=18080);p.add_argument('--output',type=Path)
 a=p.parse_args()
 build=json.loads(a.build_manifest.read_text())
 for artifact in build['artifacts']:
  actual=a.build_manifest.parent/artifact['path']
  assert digest(actual)==artifact['sha256'],'Native artifact hash differs: '+artifact['path']
 model_manifest=json.loads((a.model.parent/'manifest.json').read_text())
 assert digest(a.model)==next(x['sha256']for x in model_manifest['files']if x['file']==a.model.name),'Model weights differ'
 root=a.root.resolve();output=(a.output or root/'generation/run').resolve();output.mkdir(parents=True,exist_ok=True)
 cmd=[str(a.server.resolve()),'-m',str(a.model.resolve()),'--host','127.0.0.1','--port',str(a.port),'-t',str(a.threads),'-tb',str(a.threads),'-np',str(a.batch_size),'-c',str(a.batch_size*4096),'--no-kv-unified','-fa','on','-b','1024','-ub','128','-ngl','0','--cache-ram','0','--no-context-shift','--fit','off','--no-webui']
 launch={'server_argv':cmd,'launcher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_server_sha256':hashlib.sha256(a.server.read_bytes()).hexdigest(),'transport':'Loopback HTTP; server and client children of one parent process','output':str(output)}
 launch_file=output/'server_launch.json'
 if launch_file.exists():assert json.loads(launch_file.read_text())==launch,'Refusing changed server launch configuration'
 else:launch_file.write_text(json.dumps(launch,indent=2)+'\n')
 url='http://127.0.0.1:'+str(a.port)
 with (output/'native_server.log').open('a')as log:
  server=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
  try:
   for _ in range(240):
    if server.poll()is not None:raise RuntimeError('Native server exited '+str(server.returncode))
    try:
     with urllib.request.urlopen(url+'/health',timeout=1)as response:
      if response.status==200:break
    except Exception:time.sleep(.5)
   else:raise RuntimeError('Native server not ready')
   runner=Path(__file__).with_name('run_native_generation.py')
   command=[sys.executable,str(runner),'--input',str(root/'generation/input/generation_inputs.sqlite'),'--tokens',str(root/'generation/input/token_counts.sqlite'),'--output',str(output),'--model-manifest',str(a.model.parent/'manifest.json'),'--server-build',str(a.build_manifest.resolve()),'--protocol',str(root/'generation/scoring_protocol_frozen.json'),'--server-url',url,'--batch-size',str(a.batch_size)]
   result=subprocess.run(command)
   if result.returncode:raise SystemExit(result.returncode)
  finally:
   server.terminate()
   try:server.wait(timeout=15)
   except subprocess.TimeoutExpired:server.kill();server.wait()
if __name__=='__main__':main()
