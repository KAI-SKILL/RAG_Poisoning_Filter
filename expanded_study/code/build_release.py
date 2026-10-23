"""Package saved study artifacts without running models or changing evidence."""
from pathlib import Path
import argparse, hashlib, json, zipfile

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def selected(path,root):
    rel=path.relative_to(root)
    if '__pycache__' in rel.parts or path.suffix=='.pyc': return False
    if rel.as_posix() in {'release_manifest.json','results/case_predictions_reconstruction.tmp'}: return False
    if rel.parts[0]=='report_source' and path.name in {'main.aux','main.bbl','main.blg','main.log','main.out','main.pdf'}: return False
    return True

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--zip',type=Path,required=True)
    a=p.parse_args(); root=a.root.resolve();target=a.zip.resolve()
    if root in target.parents: raise SystemExit('ZIP destination must be outside study folder')
    files=sorted(x for x in root.rglob('*')if x.is_file()and selected(x,root))
    manifest={'status':'PACKAGED_SAVED_ARTIFACTS','study':'24 templates x 1200 attack conditions plus matched controls','scope':'Byte manifest, not execution attestation; see independent audits for decision/statistic checks.','files':[{'path':x.relative_to(root).as_posix(),'bytes':x.stat().st_size,'sha256':digest(x)}for x in files]}
    index=root/'release_manifest.json';index.write_text(json.dumps(manifest,indent=2)+'\n');files.append(index)
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True)as z:
        for x in files:z.write(x,Path(root.name)/x.relative_to(root))
    with zipfile.ZipFile(target)as z:
        bad=z.testzip()
        assert bad is None,bad
        assert len(z.infolist())==len(files)
    print(json.dumps({'status':'PASS','zip':str(target),'zip_bytes':target.stat().st_size,'zip_sha256':digest(target),'files_in_zip':len(files),'manifest_files':len(manifest['files'])},indent=2))
if __name__=='__main__':main()
