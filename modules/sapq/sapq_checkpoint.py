import os
import json
import hashlib
import time
import shutil
from datetime import datetime

class CheckpointManager:
    """
    SAPQ Checkpoint & State Management
    - Tracks AI session states to handle long-running agent workflows without losing context on crash/restart.
    - Backs up files (.bak) before modifications.
    - Validates file hash to prevent corrupt resumptions.
    """

    STATES = ["PENDING", "ANALYZING", "PATCHING", "VERIFYING", "COMPLETED", "RECOVERING", "FAILED", "RULE_CONFLICT_PAUSE"]

    def __init__(self, target_filepath, session_id=None, audit_only=False):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        self.session_id = session_id or f"sapq_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.checkpoint_dir = os.path.join(os.path.dirname(target_filepath), ".sapq_checkpoints")
        self.checkpoint_file = os.path.join(self.checkpoint_dir, f"{self.session_id}_{self.filename}.json")
        self.audit_only = audit_only

        self.state_data = {
            "session_id": self.session_id,
            "target_file": self.filename,
            "last_file_hash": None,
            "global_status": "PENDING",
            "resolved_issues": [],
            "pending_issues": [],
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }

        if not self.audit_only and not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir, exist_ok=True)

    def _calculate_hash(self):
        """Calculates SHA-256 hash of the target file."""
        if not os.path.exists(self.filepath):
            return None
        sha256 = hashlib.sha256()
        with open(self.filepath, 'rb') as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()

    def create_backup(self):
        """Creates a backup of the target file."""
        if self.audit_only:
            return None
        if not os.path.exists(self.filepath):
            return None
        backup_name = f"{self.filename}.bak_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.checkpoint_dir, backup_name)
        shutil.copy2(self.filepath, backup_path)
        return backup_path

    def load_checkpoint(self):
        """Loads an existing checkpoint if it exists."""
        if self.audit_only:
            return False
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    self.state_data = json.load(f)
                    return True
            except Exception as e:
                print(f"Failed to load checkpoint: {e}")
        return False

    def save_checkpoint(self):
        """Saves current state to the checkpoint file."""
        import tempfile
        self.state_data["updated_at"] = datetime.utcnow().isoformat() + "Z"
        if not self.audit_only:
            dir_name = os.path.dirname(self.checkpoint_file)
            fd, tmp_path = tempfile.mkstemp(dir=dir_name)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self.state_data, f, indent=2)
                os.replace(tmp_path, self.checkpoint_file)
            except Exception as e:
                os.remove(tmp_path)
                raise e

    def update_status(self, new_status, update_hash=True):
        """Updates the global status and optionally the file hash."""
        if new_status not in self.STATES:
            raise ValueError(f"Invalid state: {new_status}")
        self.state_data["global_status"] = new_status
        if update_hash:
            self.state_data["last_file_hash"] = self._calculate_hash()
        self.save_checkpoint()

    def verify_hash(self):
        """Checks if the current file hash matches the stored hash."""
        current_hash = self._calculate_hash()
        stored_hash = self.state_data.get("last_file_hash")
        return current_hash == stored_hash

    def add_resolved_issue(self, issue_type, target_node):
        """Records a successfully patched and verified issue using AST node descriptors."""
        self.state_data["resolved_issues"].append({
            "issue_type": issue_type,
            "target_node": target_node,
            "status": "COMPLETED",
            "verified_at": datetime.utcnow().isoformat() + "Z"
        })
        self.save_checkpoint()

    def clear_pending_issues(self):
        """Clears pending issues before a new analysis run."""
        self.state_data["pending_issues"] = []
        self.save_checkpoint()

    def add_pending_issue(self, issue_type, target_node, status="PENDING"):
        """Records an issue that needs to be addressed."""
        self.state_data["pending_issues"].append({
            "issue_type": issue_type,
            "target_node": target_node,
            "status": status
        })
        self.save_checkpoint()

    def get_context_prompt(self):
        """Generates a contextual prompt for the AI agent on resume."""
        prompt = f"SAPQ SESSION RECOVERY - {self.filename}\n"
        prompt += f"Status: {self.state_data['global_status']}\n\n"

        if self.state_data["resolved_issues"]:
            prompt += "ALREADY RESOLVED (DO NOT MODIFY THESE AGAIN):\n"
            for issue in self.state_data["resolved_issues"]:
                prompt += f"- [{issue['issue_type']}] {issue['target_node']}\n"
            prompt += "\n"

        if self.state_data["pending_issues"]:
            prompt += "PENDING ISSUES TO FIX:\n"
            for issue in self.state_data["pending_issues"]:
                prompt += f"- [{issue['issue_type']}] {issue['target_node']} (Status: {issue['status']})\n"

        return prompt
