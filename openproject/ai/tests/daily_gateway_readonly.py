"""Isolated acceptance server: real native GET only, provider construction forbidden."""
import sys
sys.path.insert(0, '/app')
from gateway.native import Native
from gateway.gemini import Gemini
import uvicorn

original = Native.call
def read_only(native, path, method='GET', payload=None):
    assert method == 'GET', 'NO_NATIVE_WRITE_IN_DAILY_ACCEPTANCE'
    return original(native, path, method, payload)
Native.call = read_only
def no_provider(*args, **kwargs):
    raise AssertionError('NO_PROVIDER_IN_DAILY_ACCEPTANCE')
Gemini.sdk_client = no_provider
uvicorn.run('gateway.app:app', host='0.0.0.0', port=8090, access_log=False, log_level='warning')
