"""Strict host checkpoint reads; historical milestones never supply current runtime data."""
import json
import math
import re
from pathlib import Path

def _pairs(items):
    value={}
    for key,item in items:
        if key in value:
            raise ValueError('DUPLICATE_CHECKPOINT_KEY:'+key)
        value[key]=item
    return value

def _float(value):
    number=float(value)
    if not math.isfinite(number):
        raise ValueError('NONFINITE_CHECKPOINT_NUMBER')
    return number

def _constant(value):
    raise ValueError('NONFINITE_CHECKPOINT_NUMBER')

def strict_load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=_pairs,parse_float=_float,parse_constant=_constant)

def native_baseline(checkpoint):
    if type(checkpoint.get('checkpoint_version')) is not int or checkpoint['checkpoint_version']!=2:
        raise ValueError('CHECKPOINT_V2_REQUIRED')
    data=checkpoint.get('current_data',{})
    count=data.get('native_visible_work_packages')
    fingerprint=data.get('native_fingerprint')
    version=data.get('resource_versions',{}).get('370')
    if (type(count) is not int or count<=0 or not isinstance(fingerprint,str)
            or not re.fullmatch('[a-f0-9]{64}',fingerprint)
            or type(version) is not int or version<0):
        raise ValueError('CURRENT_NATIVE_BASELINE_REQUIRED')
    return count,fingerprint,version


def validate_checkpoint(checkpoint, ledger):
    from jsonschema import Draft202012Validator, FormatChecker
    schema=strict_load(Path(__file__).with_name('checkpoint.schema.json'))
    errors=sorted(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(checkpoint),key=lambda e:str(list(e.absolute_path)))
    if errors:raise ValueError('CHECKPOINT_SCHEMA_INVALID:'+'.'.join(map(str,errors[0].absolute_path)))
    native_baseline(checkpoint)
    packages=checkpoint['consumed_approvals']['packages']
    identifiers=[operation['proposal_id'] for package in packages for operation in package['operations']]
    if packages!=ledger.get('packages') or ledger.get('further_native_write_authorization') is not False or len(identifiers)!=len(set(identifiers)):
        raise ValueError('CHECKPOINT_CONSUMED_LEDGER_MISMATCH')
    return checkpoint
