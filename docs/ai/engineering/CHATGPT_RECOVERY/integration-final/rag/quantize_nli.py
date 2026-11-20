"""One-time CPU quantization in a bounded network-none container."""
import hashlib,json,resource,time
from pathlib import Path
from onnxruntime.quantization import QuantType,quantize_dynamic
src=Path('/result/model-cache/model.onnx');dst=Path('/result/model-cache/model-quant.onnx')
assert not dst.exists()
with src.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='79f8cda2b1230585a95ea0514a6f1bd21c5c986ba0529bb3261213a3e195fa6e'
t=time.monotonic();quantize_dynamic(str(src),str(dst),weight_type=QuantType.QInt8)
with dst.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
result={'source_sha256':'79f8cda2b1230585a95ea0514a6f1bd21c5c986ba0529bb3261213a3e195fa6e',
 'quantized_sha256':sha,'bytes':dst.stat().st_size,'seconds':time.monotonic()-t,
 'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'operation':'ONNX Runtime dynamic QInt8, offline'}
Path('/result/nli-quantization.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
