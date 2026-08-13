import unittest
import os
import tempfile

from modules.sapq.sapq_python_parser import PythonASTParser
from modules.sapq.sapq_spec_matcher import SpecMatcher

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
        mockup_issues = [issue for issue in issues if issue.get("type") == "MOCKUP_HALLUCINATION"]
        self.assertEqual(len(mockup_issues), 2, "Should find 2 MOCKUP_HALLUCINATION issues")

        issue_texts = [i["issue"] for i in mockup_issues]
        self.assertTrue(any("subprocess.run called without explicit creationflags" in t for t in issue_texts))
        self.assertTrue(any("os.system used. Replace with subprocess.run" in t for t in issue_texts))

    def test_spec_matcher_detects_torsion_crossing(self):
        """
        Simulated Failure: JS file with a mismatched configuration variable value.
        Assertion Guarantee: Should flag TORSION_CROSSING errors.
        """
        specs = {
            "targetFrequency": 40,
            "active": "true" # Note: JS esprima parser reads boolean true as python boolean True or string? esprima returns a boolean.
        }

        # We need to test the boolean parsing from esprima carefully.
        # In esprima AST, false is a Literal with value False.
        # So we should expect our matcher to compare string representations: str(False) vs str("true") -> "False" != "true"
        matcher = SpecMatcher(self.bad_js_path, specs)
        issues = matcher.audit_specs()

        self.assertTrue(len(issues) > 0, "Failed to detect spec mismatches")

        torsion_issues = [issue for issue in issues if issue.get("type") == "TORSION_CROSSING"]
        self.assertTrue(len(torsion_issues) >= 1, "Should find at least 1 TORSION_CROSSING issue")

        issue_texts = [i["issue"] for i in torsion_issues]
        self.assertTrue(any("targetFrequency" in t and "40" in t for t in issue_texts))

if __name__ == '__main__':
    unittest.main()
