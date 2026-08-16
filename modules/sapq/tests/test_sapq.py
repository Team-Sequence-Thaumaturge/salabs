import sys, os
sapq_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sapq_dir not in sys.path:
    sys.path.insert(0, sapq_dir)
import unittest
import tempfile

from sapq_python_parser import PythonASTParser
from sapq_spec_matcher import SpecSemanticMatcher

class TestSAPQPhase17(unittest.TestCase):

    def setUp(self):
        # Create a temporary bad python file (missing creationflags)
        self.bad_py_fd, self.bad_py_path = tempfile.mkstemp(suffix=".py")
        bad_py_content = """
import subprocess
import os

def run_process():
    subprocess.run(["echo", "hello"]) # Missing creationflags
    os.system("dir") # Missing creationflags
"""
        with os.fdopen(self.bad_py_fd, 'w') as f:
            f.write(bad_py_content)

        # Create a temporary bad JS file (mismatched config variable)
        self.bad_js_fd, self.bad_js_path = tempfile.mkstemp(suffix=".js")
        bad_js_content = """
let targetFrequency = 60; // Should be 40
const state = { active: false }; // Should be true
"""
        with os.fdopen(self.bad_js_fd, 'w') as f:
            f.write(bad_js_content)

    def tearDown(self):
        os.remove(self.bad_py_path)
        os.remove(self.bad_js_path)

    def test_python_ast_parser_detects_mockup_hallucination(self):
        """
        Simulated Failure: Python script executing subprocess.run without creationflags.
        Assertion Guarantee: Should flag MOCKUP_HALLUCINATION.
        """
        parser = PythonASTParser(self.bad_py_path)
        issues = parser.audit_subprocess_calls()

        self.assertTrue(len(issues) > 0, "Failed to detect missing creationflags")

        # We expect 2 issues (one for subprocess.run, one for os.system)
        os_issues = [issue for issue in issues if issue.get("type") == "OS_SYSTEM_POPUP"]
        sub_issues = [issue for issue in issues if issue.get("type") == "SUBPROCESS_POPUP"]
        self.assertEqual(len(os_issues), 1, "Should find 1 OS_SYSTEM_POPUP issue")
        self.assertEqual(len(sub_issues), 1, "Should find 1 SUBPROCESS_POPUP issue")

        self.assertTrue(any("called without creationflags=0x08000000" in t for t in [i["issue"] for i in sub_issues]))
        self.assertTrue(any("os.system used. Use subprocess" in t for t in [i["issue"] for i in os_issues]))

    def test_spec_matcher_detects_torsion_crossing(self):
        """
        Simulated Failure: JS file with a mismatched configuration variable value.
        Assertion Guarantee: Should flag SPEC_ALIGNMENT_MISMATCH or SPEC_MISSING.
        """
        with open(self.bad_js_path, 'r', encoding='utf-8') as f:
            js_code = f.read()
        matcher = SpecSemanticMatcher("target frequency = 40", self.bad_js_path, js_code)
        issues = matcher.audit_code_alignment()

        self.assertTrue(len(issues) > 0, "Failed to detect spec mismatches")

        spec_issues = [issue for issue in issues if issue.get("type") in ("SPEC_ALIGNMENT_MISMATCH", "SPEC_ALIGNMENT_MISSING")]
        self.assertTrue(len(spec_issues) >= 1, "Should find at least 1 SPEC_ALIGNMENT_MISMATCH issue")

        issue_texts = [i["issue"] for i in spec_issues]
        self.assertTrue(any("target frequency" in t and "40" in t for t in issue_texts))

if __name__ == '__main__':
    unittest.main()
