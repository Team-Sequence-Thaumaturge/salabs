import unittest
import os
import sys

# Ensure modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sapq_ast_parser import ASTParser
from sapq_security_guard import SAPQSecurityGuard

class TestSAPQSecurityGuard(unittest.TestCase):

    def setUp(self):
        # Create temporary files for testing
        self.js_file = "temp_test_sec_guard.js"
        self.py_file = "temp_test_sec_guard.py"

    def tearDown(self):
        if os.path.exists(self.js_file):
            os.remove(self.js_file)
        if os.path.exists(self.py_file):
            os.remove(self.py_file)

    def test_js_unsanitized_flow(self):
        code = """
        let params = new URLSearchParams(location.search);
        let user_input = params.get('q');
        document.getElementById('res').innerHTML = user_input; // Sink
        """
        with open(self.js_file, 'w') as f:
            f.write(code)
        parser = ASTParser(self.js_file)
        guard = SAPQSecurityGuard(self.js_file, parser)
        report = guard.analyze()
        self.assertTrue(any(i['type'] == 'UNSANITIZED_DATA_FLOW' for i in report['issues']))
        self.assertEqual(report['metrics']['UNSANITIZED_DATA_FLOW'], 1)

    def test_js_sanitized_flow(self):
        code = """
        let params = new URLSearchParams(location.search);
        let user_input = params.get('q');
        let safe_input = escapeHTML(user_input); // Sanitizer
        document.getElementById('res').innerHTML = safe_input; // Sink
        """
        with open(self.js_file, 'w') as f:
            f.write(code)
        parser = ASTParser(self.js_file)
        guard = SAPQSecurityGuard(self.js_file, parser)
        report = guard.analyze()
        self.assertFalse(any(i['type'] == 'UNSANITIZED_DATA_FLOW' for i in report['issues']))

    def test_js_hardcoded_credential_and_plaintext(self):
        code = """
        const API_KEY = "12345abcdef";
        const url = "http://api.example.com";
        """
        with open(self.js_file, 'w') as f:
            f.write(code)
        parser = ASTParser(self.js_file)
        guard = SAPQSecurityGuard(self.js_file, parser)
        report = guard.analyze()
        self.assertTrue(any(i['type'] == 'HARDCODED_CREDENTIAL' for i in report['issues']))
        self.assertTrue(any(i['type'] == 'PLAINTEXT_PROTOCOL' for i in report['issues']))

    def test_python_unsafe_regex(self):
        code = """
import re
pattern = re.compile(r"([a-z]+)+") # Unsafe nested quantifier
        """
        with open(self.py_file, 'w') as f:
            f.write(code)
        parser = ASTParser(self.py_file)
        guard = SAPQSecurityGuard(self.py_file, parser)
        report = guard.analyze()
        self.assertTrue(any(i['type'] == 'UNSAFE_REGEX' for i in report['issues']))

    def test_python_unsanitized_flow(self):
        code = """
import sys
import os

user_input = sys.argv[1]
os.system(user_input) # Sink
        """
        with open(self.py_file, 'w') as f:
            f.write(code)
        parser = ASTParser(self.py_file)
        guard = SAPQSecurityGuard(self.py_file, parser)
        report = guard.analyze()
        self.assertTrue(any(i['type'] == 'UNSANITIZED_DATA_FLOW' for i in report['issues']))

if __name__ == '__main__':
    unittest.main()
