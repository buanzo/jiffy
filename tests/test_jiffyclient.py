import os
import unittest
import textwrap
import sys
import types
import tempfile

# Ensure the repository root is on the path so modules can be imported when
# tests are executed from arbitrary working directories.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Stub out the bundled 'requests' module so importing JiffyClient does not
# require its heavy dependencies during testing.
sys.modules['requests'] = types.SimpleNamespace(Session=lambda *a, **k: object())

from JiffyClient import (
    JiffyClient,
    JiffyConfigError,
    JiffyVerificationError,
)

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
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            tmpconf = os.path.join(tmpdir, 'JiffyClient.conf')
            with open(tmpconf, 'w') as fh:
                fh.write('[DEFAULT]\nServer=https://example.com\nServerPubkeyId=ABC123\n')
            try:
                with self.assertRaises(JiffyConfigError):
                    self.jc.readConfig()
            finally:
                os.chdir(cwd)

    def test_read_config_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            tmpconf = os.path.join(tmpdir, 'JiffyClient.conf')
            with open(tmpconf, 'w') as fh:
                fh.write('[DEFAULT]\nServer=https://example.com/\nServerPubkeyId=ABC123\n\n[jiffyclient]\nLocalPubkeyId=KEYID123\n')
            try:
                self.jc.readConfig()
                self.assertEqual(self.jc.SERVER_URL, 'https://example.com')
                self.assertEqual(self.jc.SERVER_KEY, 'ABC123')
                self.assertEqual(self.jc.CLIENT_KEY, 'KEYID123')
            finally:
                os.chdir(cwd)

    def test_gpg_verify_failure_raises(self):
        self.jc.GPG = types.SimpleNamespace(verify=lambda text: False)
        with self.assertRaises(JiffyVerificationError):
            self.jc.gpgVerifyAndExtractText('data')

if __name__ == '__main__':
    unittest.main()
