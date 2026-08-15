import unittest
import os
from modules.sapq.sapq_ast_parser import ASTParser

class TestSAPQPythonAST(unittest.TestCase):
    def test_python_ast_extraction(self):
        code = """
def test_func(arg1):
    local_var = 42
    return arg1 + local_var + global_var
"""
        with open("dummy_test.py", "w") as f:
            f.write(code)

        parser = ASTParser("dummy_test.py")
        usages = parser.get_all_identifier_usages()

        # arg1, local_var, global_var should be in usages.
        # test_func is the declaration so it shouldn't be counted strictly,
        # but the AST adapter might grab all. We just care that it finds usages.
        self.assertTrue("arg1" in usages)
        self.assertTrue("local_var" in usages)
        self.assertTrue("global_var" in usages)

        os.remove("dummy_test.py")

if __name__ == '__main__':
    unittest.main()
