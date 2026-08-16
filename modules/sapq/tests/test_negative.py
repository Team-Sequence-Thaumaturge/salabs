import os
import sys

# Add parent directory to path to import sapq modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sapq.sapq_python_parser import PythonASTParser
from sapq.sapq_spec_matcher import SpecSemanticMatcher

def create_bad_python_script(filepath):
    code = """
import subprocess
import os

def run_task():
    # Bad: subprocess without creationflags
    subprocess.run(["echo", "hello"])

    # Bad: os.system
    os.system("dir")
"""
    with open(filepath, 'w') as f:
        f.write(code)

def create_bad_js_script(filepath):
    code = """
const target_frequency = 50; // Spec requires 40!
"""
    with open(filepath, 'w') as f:
        f.write(code)

def test_negative_cases():
    test_dir = os.path.dirname(__file__)
    bad_py = os.path.join(test_dir, 'bad_script.py')
    bad_js = os.path.join(test_dir, 'bad_script.js')

    print("🧪 Running Phase 17.4 Negative Test Suite...")

    # Generate bad files
    create_bad_python_script(bad_py)
    create_bad_js_script(bad_js)

    # 1. Test Python Popup Vulnerability
    print("Testing Python Parser...")
    py_parser = PythonASTParser(bad_py)
    py_warnings = py_parser.audit_subprocess_calls()

    assert len(py_warnings) == 2, f"Expected 2 python warnings, got {len(py_warnings)}"
    assert any("OS_SYSTEM_POPUP" in w['issue'] for w in py_warnings)
    assert any("SUBPROCESS_POPUP" in w['issue'] for w in py_warnings)
    print("✅ Python Parser Negative Tests Passed!")

    try:
        # 2. Test Spec Alignment Mismatch
        print("Testing Spec Matcher...")
        raw_spec = "target frequency = 40"
        with open(bad_js, 'r') as f:
            js_code = f.read()

        matcher = SpecSemanticMatcher(raw_spec, bad_js, js_code)
        spec_warnings = matcher.audit_code_alignment()

        assert len(spec_warnings) == 1, f"Expected 1 spec warning, got {len(spec_warnings)}"
        assert "SPEC_ALIGNMENT_MISMATCH" in spec_warnings[0]['issue']
        print("✅ Spec Matcher Negative Tests Passed!")
        print("🎉 All negative tests passed successfully.")
    finally:
        # Cleanup
        if os.path.exists(bad_py):
            os.remove(bad_py)
        if os.path.exists(bad_js):
            os.remove(bad_js)

if __name__ == "__main__":
    test_negative_cases()
