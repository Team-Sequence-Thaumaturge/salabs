import os
import json
from datetime import datetime

class SAPQLogger:
    """
    SAPQ Append-Only Logging System
    - Records phase transitions, scores, and specific errors in JSON Lines (.jsonl) format.
    - Used for post-mortem debugging to trace when and where an AI agent introduced a regression.
    """

    def __init__(self, target_filepath, session_id):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        self.session_id = session_id

        # Determine log directory relative to the target file or use a global one
        self.log_dir = os.path.join(os.path.dirname(target_filepath), ".sapq_logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        # Daily log file
        date_str = datetime.utcnow().strftime('%Y%m%d')
        self.log_file = os.path.join(self.log_dir, f"sapq_audit_{date_str}.jsonl")

    def _write_log(self, event_type, details):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "target_file": self.filename,
            "event_type": event_type,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + "\n")

    def log_session_start(self):
        self._write_log("SESSION_START", {"message": "Audit session initialized."})

    def log_preflight_result(self, is_valid, errors):
        self._write_log("PREFLIGHT_GUARD", {
            "status": "PASSED" if is_valid else "FAILED",
            "error_count": len(errors),
            "errors": errors
        })

    def log_audit_completion(self, score, discontinuities, zombie_nodes):
        self._write_log("AUDIT_COMPLETED", {
            "integrity_score": score,
            "discontinuities_found": len(discontinuities),
            "zombie_nodes_found": len(zombie_nodes),
            "top_issues": [d["issue"] for d in discontinuities[:3]] + [z["issue"] for z in zombie_nodes[:3]]
        })

    def log_error(self, message):
        self._write_log("ERROR", {"message": message})
