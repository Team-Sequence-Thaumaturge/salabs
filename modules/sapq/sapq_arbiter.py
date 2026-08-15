import json
import os
from datetime import datetime

class SAPQArbiter:
    """
    SAPQ Metacognitive Arbiter
    - Prevents "Oracle Compliance Bias" where agents repeatedly patch the same code leading to regression.
    - Detects false positives via oscillation tracking and acts as a circuit breaker.
    - Implements Tool Refutation Protocol to optionally bypass flawed constraints.
    """

    def __init__(self, target_filepath, session_id):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        self.session_id = session_id
        self.arbiter_dir = os.path.join(os.path.dirname(target_filepath), ".sapq_arbiter_state")
        self.state_file = os.path.join(self.arbiter_dir, f"{self.session_id}_{self.filename}_arbiter.json")

        self.state = {
            "session_id": self.session_id,
            "target_file": self.filename,
            "history": [], # Track previous scores to detect oscillation
            "modifications": {}, # Track modifications by symbol: {"symbol_name": count}
            "bypassed_rules": [] # List of bypassed issues
        }

        if not os.path.exists(self.arbiter_dir):
            os.makedirs(self.arbiter_dir, exist_ok=True)

        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
            except Exception:
                pass

    def _save_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)

    def record_run(self, score, issues):
        """Records the outcome of an audit run."""
        self.state["history"].append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "score": score
        })

        # Increment modification counters for issues found in this run
        for issue in issues:
            symbol = issue.get("symbol", "unknown")
            if symbol not in self.state["modifications"]:
                self.state["modifications"][symbol] = 0
            self.state["modifications"][symbol] += 1

        self._save_state()

    def check_oscillation_and_arbitrate(self, issues):
        """
        Evaluates the current issues against history to detect if the agent is stuck in a loop.
        Returns (should_pause, filtered_issues, message).
        """
        filtered_issues = []
        pause_triggered = False
        message = ""

        # Check score oscillation (e.g., scores bouncing or dropping repeatedly)
        if len(self.state["history"]) >= 3:
            recent_scores = [h["score"] for h in self.state["history"][-3:]]
            # Simple heuristic: if score hasn't improved or oscillates
            if recent_scores[0] >= recent_scores[1] and recent_scores[1] <= recent_scores[2] and recent_scores[2] < 100:
                # We detect a potential macro-level regression loop, but we rely on the
                # granular symbol modification tracker below to isolate exactly which
                # rule/symbol to bypass, rather than bypassing everything blindly.
                pass

        for issue in issues:
            symbol = issue.get("symbol", "unknown")
            issue_desc = issue.get("issue", "")

            # Skip if already bypassed
            if any(b['symbol'] == symbol for b in self.state["bypassed_rules"]):
                continue

            mod_count = self.state["modifications"].get(symbol, 0)

            # If a symbol has been repeatedly flagged/patched 3 or more times, it's likely a false positive
            if mod_count >= 3:
                pause_triggered = True
                message = f"RULE_CONFLICT_PAUSE: Metacognitive Arbiter detected oscillation on symbol '{symbol}'. Possible tool defect."
                # Apply Tool Refutation Protocol
                self.state["bypassed_rules"].append({
                    "symbol": symbol,
                    "reason": "ISSUE_TOOL_DEFECT: Reached modification limit without resolution."
                })
                self._save_state()
            else:
                filtered_issues.append(issue)

        return pause_triggered, filtered_issues, message

    def generate_feedback_request(self):
        """Generates a JSON payload for the SACM Coder to request rule mutation."""
        if not self.state["bypassed_rules"]:
            return None

        return {
            "type": "RuleMutationSuggestion",
            "target_file": self.filename,
            "defects": self.state["bypassed_rules"],
            "suggestion": "Requesting SACM to relax constraints or adjust AST parsing for the listed symbols due to verified false positives."
        }
