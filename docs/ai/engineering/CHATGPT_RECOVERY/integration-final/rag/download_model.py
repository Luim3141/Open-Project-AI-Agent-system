"""Fetch fixed public model assets only; verify publisher LFS SHA256 before use."""
import hashlib,json,urllib.request
from pathlib import Path

root=Path(__file__).parent/'model-cache';root.mkdir(parents=True,exist_ok=True)
revision='0a71e92a985b6e1ad1828cf67ce9c459639c1dca'
assets={'model.onnx':('79f8cda2b1230585a95ea0514a6f1bd21c5c986ba0529bb3261213a3e195fa6e',428127016),
        'tokenizer.json':('b2116c05e7305eea30394284760789681c5b3440dd4cd9a8c77539da68f9e8a6',17082854)}
for name,(sha,size) in assets.items():
 target=root/name
 if not target.exists():
  tmp=target.with_suffix(target.suffix+'.partial')
  url=f'https://huggingface.co/MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli/resolve/{revision}/onnx/{name}'
  with urllib.request.urlopen(url,timeout=120) as response,tmp.open('wb') as stream:
   while chunk:=response.read(1024*1024):stream.write(chunk)
  assert tmp.stat().st_size==size
  with tmp.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha
  tmp.replace(target)
 with target.open('rb') as stream:assert target.stat().st_size==size and hashlib.file_digest(stream,'sha256').hexdigest()==sha
print(json.dumps({'model':'MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli','revision':revision,'license':'MIT','assets':{k:{'sha256':v[0],'bytes':v[1]} for k,v in assets.items()},'scope':'PUBLIC MODEL ASSETS ONLY; no corpus sent'}))
