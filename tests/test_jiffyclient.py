import os
import unittest
import textwrap
import sys
import types

# Stub out the bundled 'requests' module so importing JiffyClient does not
# require its heavy dependencies during testing.
sys.modules['requests'] = types.SimpleNamespace(Session=lambda *a, **k: object())

from JiffyClient import JiffyClient

class FakeVerified:
    TRUST_FULLY = 3
    def __init__(self, ts, trust_level=TRUST_FULLY):
        self.trust_level = trust_level
        self.sig_timestamp = ts

class TestJiffyClient(unittest.TestCase):
    def setUp(self):
        self.jc = JiffyClient()

    def test_extract_signed_text_valid(self):
        ts = 1729275301
        verified = FakeVerified(ts)
        message = textwrap.dedent("""\
        -----BEGIN PGP SIGNED MESSAGE-----
        Hash: SHA256

        hello
        -----BEGIN PGP SIGNATURE-----
        Version: 1

        """)
        result = self.jc.extractSignedText(verified, message)
        self.assertEqual(result, "hello")
        self.assertEqual(self.jc.lastInSigTimestamp, ts)
        self.assertTrue(self.jc.lastInSigTimestamp_text)

    def test_read_config_missing_local_key(self):
        tmpconf = os.path.join(os.getcwd(), 'JiffyClient.conf')
        with open(tmpconf, 'w') as fh:
            fh.write('[DEFAULT]\nServer=https://example.com\nServerPubkeyId=ABC123\n')
        try:
            with self.assertRaises(SystemExit) as cm:
                self.jc.readConfig()
            self.assertEqual(cm.exception.code, 7)
        finally:
            os.remove(tmpconf)

    def test_read_config_ok(self):
        tmpconf = os.path.join(os.getcwd(), 'JiffyClient.conf')
        with open(tmpconf, 'w') as fh:
            fh.write('[DEFAULT]\nServer=https://example.com/\nServerPubkeyId=ABC123\n\n[jiffyclient]\nLocalPubkeyId=KEYID123\n')
        try:
            self.jc.readConfig()
            self.assertEqual(self.jc.SERVER_URL, 'https://example.com')
            self.assertEqual(self.jc.SERVER_KEY, 'ABC123')
            self.assertEqual(self.jc.CLIENT_KEY, 'KEYID123')
        finally:
            os.remove(tmpconf)

if __name__ == '__main__':
    unittest.main()
