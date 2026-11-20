"""Run a bounded check and retain its actual source/image/environment provenance."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).parent/'checks'


def source_snapshot():
    files={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT/'openproject/ai').rglob('*')
        if p.is_file() and p.suffix in {'.py','.js','.rb','.erb','.yml'} and '__pycache__' not in str(p)}
    assert files and all(len(v)==64 for v in files.values())
    return {'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        'includes_uncommitted_source':True,'files':files,
        'manifest_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True);parser.add_argument('--environment',required=True)
    parser.add_argument('--image',action='append',default=[]);parser.add_argument('--timeout',type=int,default=600)
    parser.add_argument('command',nargs=argparse.REMAINDER);args=parser.parse_args()
    argv=args.command[1:] if args.command[:1]==['--'] else args.command
    assert argv and args.name.replace('-','').replace('_','').isalnum()
    OUT.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target=OUT/(args.name+'-'+stamp)
    before=source_snapshot();start=time.time()
    result=subprocess.run(argv,capture_output=True,cwd=ROOT,timeout=args.timeout)
    target.with_suffix('.log').write_bytes(result.stdout+result.stderr)
    after=source_snapshot()
    record={'started_utc':datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),
        'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'command':argv,'environment':args.environment,'tested_image_digests':args.image,
        'source':before,'source_changed_during_check':before['manifest_sha256']!=after['manifest_sha256'],
        'exit_code':result.returncode,'outcome':'PASS' if result.returncode==0 else 'FAIL',
        'evidence':str(target.with_suffix('.log').relative_to(ROOT)).replace('\\','/')}
    target.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print((result.stdout+result.stderr).decode(errors='replace')[-2200:])
    print(json.dumps({k:record[k] for k in ['outcome','exit_code','environment','source_changed_during_check','evidence']}))
    sys.exit(result.returncode)
