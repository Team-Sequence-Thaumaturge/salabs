import sys, os
sys.path.insert(0, r"C:\stella.os\Quanxs\sair")
sys.path.insert(0, r"C:\stella.os\Quanxs\sair\SAPQ")
import unittest
import os
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

        self.assertTrue(any("creationflags" in t for t in [i["issue"] for i in sub_issues]))
        self.assertTrue(any("os.system used" in t for t in [i["issue"] for i in os_issues]))

    def test_spec_matcher_detects_torsion_crossing(self):
        """
        Simulated Failure: JS file with a mismatched configuration variable value.
        Assertion Guarantee: Should flag SPEC_ALIGNMENT_MISMATCH errors.
        """
        specs = {
            "targetFrequency": 40,
            "active": "true" # Note: JS esprima parser reads boolean true as python boolean True or string? esprima returns a boolean.
        }

        # We need to test the boolean parsing from esprima carefully.
        # In esprima AST, false is a Literal with value False.
        # So we should expect our matcher to compare string representations: str(False) vs str("true") -> "False" != "true"
        with open(self.bad_js_path, 'r', encoding='utf-8') as f:
            code_content = f.read()

        # SpecSemanticMatcher takes raw_spec, target_filepath, code_content. We mock raw_spec for now
        raw_spec = "targetFrequency = 40\nactive = true"
        matcher = SpecSemanticMatcher(raw_spec, self.bad_js_path, code_content)
        issues = matcher.audit_code_alignment()

        self.assertTrue(len(issues) > 0, "Failed to detect spec mismatches")

        torsion_issues = [issue for issue in issues if issue.get("type") == "SPEC_ALIGNMENT_MISMATCH"]
        self.assertTrue(len(torsion_issues) >= 1, "Should find at least 1 SPEC_ALIGNMENT_MISMATCH issue")

        issue_texts = [i["issue"] for i in torsion_issues]
        self.assertTrue(any("targetFrequency" in t and "40" in t for t in issue_texts))

if __name__ == '__main__':
    unittest.main()
