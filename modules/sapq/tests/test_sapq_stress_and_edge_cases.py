import unittest
import os
import sys
import time
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sapq_engine import SAPQEngine, audit_file
from multi_vector_parser import MultiVectorCrossParsingAuditEngine
from sapq_spatial_projector import SpatialProjector
from sapq_ast_parser import ASTParser

class TestSAPQStressAndEdgeCases(unittest.TestCase):

    def setUp(self):
        self.large_file = "large_test.py"
        self.empty_file = "empty_test.py"
        self.comment_file = "comment_test.js"
        self.single_token_file = "single_token.py"

        # 1. 10,000 lines of fake AST code
        with open(self.large_file, "w") as f:
            for i in range(10000):
                f.write(f"function func_{i}() {{}}\n")

        # 2. Edge Cases
        with open(self.empty_file, "w") as f:
            pass

        with open(self.comment_file, "w") as f:
            f.write("// Just a comment\n/* Block comment */")

        with open(self.single_token_file, "w") as f:
            f.write("test_token")

        self.files_to_cleanup = [self.large_file, self.empty_file, self.comment_file, self.single_token_file]

    def tearDown(self):
        for f in self.files_to_cleanup:
            if os.path.exists(f):
                os.remove(f)

    def test_large_file_stress(self):
        """Test 10,000 lines of code to check for memory leaks and processing delays."""
        start_time = time.time()

        engine = MultiVectorCrossParsingAuditEngine(self.large_file)
        report = engine.execute_vector_end_trajectory_linking()

        elapsed = time.time() - start_time

        # It should complete in a reasonable time (e.g., < 5 seconds)
        self.assertTrue(elapsed < 10.0, f"Stress test took too long: {elapsed:.2f}s")
        self.assertEqual(report["total_lines"], 10000)
        self.assertEqual(report["vector_nodes"]["V1_Forward_Count"], 10000)

    def test_edge_cases(self):
        """Test empty file, comment file, and single token file."""
        # Empty File
        engine = MultiVectorCrossParsingAuditEngine(self.empty_file)
        report = engine.execute_vector_end_trajectory_linking()
        self.assertEqual(report["total_lines"], 0)

        # Comment File
        engine2 = MultiVectorCrossParsingAuditEngine(self.comment_file)
        report2 = engine2.execute_vector_end_trajectory_linking()
        self.assertEqual(report2["total_lines"], 2)

        # Single Token File
        engine3 = MultiVectorCrossParsingAuditEngine(self.single_token_file)
        report3 = engine3.execute_vector_end_trajectory_linking()
        self.assertEqual(report3["total_lines"], 1)

        # AST Parser on broken code
        with open("broken.js", "w") as f:
            f.write("function abc( { let x = 5;")
        self.files_to_cleanup.append("broken.js")

        ast_parser = ASTParser("broken.js")
        res = ast_parser.detect_scope_undeclared_symbols()
        self.assertEqual(res, [])

        engine_broken = MultiVectorCrossParsingAuditEngine("broken.js")
        # Overwrite content to force an exception
        engine_broken.lines = None
        report_broken = engine_broken.execute_vector_end_trajectory_linking()
        self.assertIn("error_tensor", report_broken)

    def test_spatial_projector_tensors(self):
        """Test tensor output format to ensure Float32Array compliance (no NaN/Infinity)."""
        projector = SpatialProjector(self.large_file)
        tensors = projector.generate_tensors()

        self.assertIn("positions", tensors)
        self.assertIn("colors", tensors)
        self.assertIn("torsionTensors", tensors)

        # Check for NaN and Infinity in arrays
        for key in ["positions", "colors", "torsionTensors", "reconciliationVectors", "gravitySinks"]:
            array = tensors[key]
            for val in array:
                self.assertFalse(math.isnan(val), f"NaN found in {key}")
                self.assertFalse(math.isinf(val), f"Infinity found in {key}")

if __name__ == '__main__':
    unittest.main()
