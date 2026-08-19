import json

class SAPQArbiter:
    """
    Phase 21: LLM Interrogation & Self-Healing Loop
    - Ingests critical defects (like Phase 20 MISSING_INTENDED_FEATURE).
    - Generates strict, JSON-formatted 'Interrogation Dossiers' to force the LLM to justify or fix omissions without "lazy rationalization".
    - Acts as a circuit breaker (RULE_CONFLICT_PAUSE) against infinite patching loops.
    """
    def __init__(self, max_retries=3, session_id="default"):
        import os
        self.max_retries = max_retries
        self.session_id = session_id
        self.patch_history = []
        self.log_file = f".sapq_logs/arbiter_{self.session_id}.json"

        # Load persisted state for CLI usage
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as log_f:
                    self.patch_history = json.load(log_f)
            except Exception:
                pass

    def log_patch_attempt(self, score, issues_count):
        """Records a patch attempt to detect oscillation / infinite loops."""
        import os
        self.patch_history.append({"score": score, "issues_count": issues_count})
        # Persist state
        os.makedirs(".sapq_logs", exist_ok=True)
        with open(self.log_file, "w") as log_f:
            json.dump(self.patch_history, log_f)

    def check_oscillation(self):
        """Circuit Breaker: Returns True if the AI is stuck in an infinite loop of fixing and breaking."""
        if len(self.patch_history) < self.max_retries:
            return False

        recent = self.patch_history[-self.max_retries:]
        # If the issue count never reaches 0 and score oscillates or remains static
        scores = [h["score"] for h in recent]
        if max(scores) == min(scores) and recent[-1]["issues_count"] > 0:
            return True
        return False

    def generate_interrogation_dossier(self, target_filename, baseline_issues=None, generic_issues=None):
        """
        Generates a strict JSON prompt designed for LLM consumption.
        It explicitly forbids arbitrary rationalization and demands concrete code fixes or systemic proofs.
        """
        baseline_issues = baseline_issues or []
        generic_issues = generic_issues or []

        all_issues = baseline_issues + generic_issues

        if not all_issues:
            return None

        if self.check_oscillation():
            return json.dumps({
                "type": "RULE_CONFLICT_PAUSE",
                "directive": "ABORT_CURRENT_STRATEGY",
                "message": "Oracle Compliance Bias Detected. You are looping. Stop blindly applying the same patch. Issue a Tool Refutation Protocol to bypass if this is a false positive."
            }, indent=2)

        dossier = {
            "type": "SAPQ_INTERROGATION",
            "target": target_filename,
            "directive": "You must provide a Git Merge Diff to restore the missing topological nodes, OR provide a systemic proof justifying their removal.",
            "strict_rules": [
                "DO NOT provide conversational rationalizations (e.g., 'It seems ok because...').",
                "DO NOT blindly stub the function back. Restore its actual AST semantic capability (Reads State, Writes DOM)."
            ],
            "topological_holes": []
        }

        for issue in baseline_issues:
            dossier["topological_holes"].append({
                "missing_role": issue.get("role_signature", "UNKNOWN"),
                "original_function_context": issue.get("original_functions", []),
                "demand": "Restore this semantic trajectory in the target file."
            })

        for issue in generic_issues:
            # Handle standard structural issues like GHOST_NODE, TORSION_CROSSING, etc.
            dossier["topological_holes"].append({
                "issue_type": issue.get("issue", "UNKNOWN_ERROR").split(':')[0],
                "detail": issue.get("issue", ""),
                "demand": "Fix the structural contradiction."
            })

        return json.dumps(dossier, indent=2)
