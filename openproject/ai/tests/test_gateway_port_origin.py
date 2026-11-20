import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from gateway.app import Security


class GatewayPortOriginTests(unittest.TestCase):
    def test_new_loopback_origin_and_untrusted_origins(self):
        async def health(request):
            return JSONResponse({'ok': True})

        hosts = ['127.0.0.1:18089', 'localhost:18089', 'gateway:8090']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config.json').write_text(json.dumps({'hosts': hosts}))
            app = Security(Starlette(routes=[Route('/health', health)]), root, Mock(), {}, None)
            with TestClient(app, base_url='http://127.0.0.1:18089') as client:
                for origin in ('http://127.0.0.1:18089', 'http://localhost:18089', 'http://127.0.0.1:8090'):
                    self.assertEqual(client.get('/health', headers={'Origin': origin}).status_code, 200)
                for origin in ('http://example.com:18089', 'http://gateway:8090', 'http://127.0.0.1:18088'):
                    self.assertEqual(client.get('/health', headers={'Origin': origin}).status_code, 403)
                self.assertEqual(client.get('/health', headers={'Host': 'evil.invalid'}).status_code, 403)


if __name__ == '__main__':
    unittest.main()
