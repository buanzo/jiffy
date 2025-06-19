import sys
import types
import unittest
import asyncio
import os

# Ensure repository root on path for imports when tests are run from other dirs.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Stub out aiohttp so AsyncJiffyClient can be imported without heavy deps
class FakeResponse:
    def __init__(self, text):
        self._text = text
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    async def text(self):
        return self._text

class FakeSession:
    def __init__(self, text):
        self._text = text
    def get(self, *a, **kw):
        return FakeResponse(self._text)
    async def close(self):
        pass

sys.modules['aiohttp'] = types.SimpleNamespace(ClientSession=lambda *a, **k: FakeSession('signed'))
sys.modules['requests'] = types.SimpleNamespace(Session=lambda *a, **k: object())

from async_jiffyclient import AsyncJiffyClient

class TestAsyncJiffyClient(unittest.TestCase):
    def setUp(self):
        self.client = AsyncJiffyClient()
        self.client.SERVER_URL = 'https://example.com'
        self.client.gpgVerifyAndExtractText = lambda data: data
    def tearDown(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.client.close())

    def test_get_server_version_async(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.client.getServerVersion_async())
        self.assertEqual(self.client.SERVER_VERSION, 'signed')

if __name__ == '__main__':
    unittest.main()
