import numpy as np

class OmniWorkslopGuard:
    @staticmethod
    def audit(tensor_state, raw_data, mime_type):
        """
        Detects AI Workslop patterns deterministically:
        1. Silent Failure & Ghost Sink
        2. Zombie Wrapper & Semantic Leaching
        3. Hallucination / Degenerate State
        """
        issues = []
        S_matrix = tensor_state.S_matrix

        # 1. Hallucination / Degenerate State
        # Check for NaN or Inf in the S_matrix tensor
        is_degenerate = False
        if len(S_matrix) > 0 and (np.any(np.isnan(S_matrix)) or np.any(np.isinf(S_matrix))):
            is_degenerate = True
            issues.append({"type": "DEGENERATE_STATE", "details": "NaN or Inf values detected in tensor state."})

        # 2. Silent Failure & Ghost Sink (AST heuristic for Python/JS)
        # In a real environment, we'd use ASTParser, but doing simple static heuristic for demonstration
        if mime_type == "text/plain" and isinstance(raw_data, str):
            if "except:" in raw_data:
                except_parts = raw_data.split("except:")[-1].split('\n')
                if len(except_parts) > 1 and "pass" in except_parts[1]:
                    issues.append({"type": "SILENT_FAILURE", "details": "Empty except block detected (Ghost Sink)."})
            elif "catch" in raw_data and "{}" in raw_data.replace(" ", ""):
                issues.append({"type": "SILENT_FAILURE", "details": "Empty catch block detected (Ghost Sink)."})

        # 3. Zombie Wrapper & Semantic Leaching
        # Detecting redundant wrapper functions via simple pattern heuristics
        semantic_leach_score = 0.0
        if mime_type == "text/plain" and isinstance(raw_data, str):
            if "def wrapper(" in raw_data and "return" in raw_data and "wrapper" in raw_data:
                # Basic simulated check
                semantic_leach_score = 0.8
                issues.append({"type": "ZOMBIE_WRAPPER", "details": "Redundant dummy wrapper detected."})

        # Calculate Torsion Deviation (Simulated based on invariants mismatch or tensor norm)
        torsion_deviation = 0.0
        if not tensor_state.invariants.get("valid", True):
            torsion_deviation = 1.0
        elif len(S_matrix) > 0 and not is_degenerate:
            torsion_deviation = min(1.0, np.linalg.norm(S_matrix) / (len(S_matrix) * 100 + 1e-9))

        # Overall Workslop Index (0.0 to 1.0)
        workslop_index = min(1.0, (len(issues) * 0.3) + semantic_leach_score * 0.5 + torsion_deviation * 0.2)

        return {
            "workslop_index": workslop_index,
            "semantic_leach_score": semantic_leach_score,
            "torsion_deviation": torsion_deviation,
            "issues": issues
        }
