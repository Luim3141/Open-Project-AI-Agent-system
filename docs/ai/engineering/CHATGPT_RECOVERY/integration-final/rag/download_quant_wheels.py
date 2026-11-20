"""Download exactly two verified public wheels for an isolated conversion."""
import hashlib,json,urllib.request
from pathlib import Path
root=Path(__file__).parent/'model-cache'/'wheels';root.mkdir(parents=True,exist_ok=True)
urls={
 'onnx-1.23.2-cp312-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl':('https://files.pythonhosted.org/packages/87/56/21509a657f9a73ab0ca307d325043f49ca6c4ff6bf79edeb9e159190d44d/onnx-1.23.2-cp312-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl','7abf381d278f31ac62487fddedc9dd42da842dce94d5d43536836ee3efdf4a2b'),
 'ml_dtypes-0.6.0-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl':('https://files.pythonhosted.org/packages/1c/b1/1831dd8c9b06c013085d31a2ac4f03392d43bd36bfc6ff591a08bcedc1cf/ml_dtypes-0.6.0-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl','8f490c003369ce60e514a0c3b12374f05274c101fee1bead6740ec8a564032b0')}
for name,(url,expected) in urls.items():
 path=root/name
 if not path.exists():
  tmp=path.with_suffix('.partial')
  with urllib.request.urlopen(url,timeout=90) as src,tmp.open('wb') as dst:
   while chunk:=src.read(1048576):dst.write(chunk)
  with tmp.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
  tmp.replace(path)
 with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
print(json.dumps({name:sha for name,(_,sha) in urls.items()}))
