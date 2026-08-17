import unittest
import os
import sys

from sapq_python_parser import PythonASTParser

class TestSAPQPythonAST(unittest.TestCase):
    def test_python_ast_subprocess_detection(self):
        code = """
import subprocess
import os

def test_func():
    subprocess.run(["echo", "hello"])
    os.system("echo popup")
"""
        test_file = "dummy_test_subprocess.py"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            parser = PythonASTParser(test_file)
            issues = parser.audit_subprocess_calls()
            self.assertTrue(len(issues) >= 2, "Should find at least 2 subprocess/os.system issues")
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
    unittest.main()
