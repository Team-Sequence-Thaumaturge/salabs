import ast
import psutil
import os
import sys

class PythonASTParser:
    """
    Phase 17.1: Python/OS AST Multi-Language Parser
    - Parse and audit Python backend scripts using Python's native `ast`.
    - Detect `subprocess.run`, `subprocess.Popen`, and `os.system` calls.
    - Enforce `creationflags=0x08000000` (CREATE_NO_WINDOW) to prevent Windows popups.
    - OS-level process audits (`psutil`) to detect duplicate background Python daemon scripts.
    """
    def __init__(self, target_filepath):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        self.code = ""
        self.ast_tree = None

        try:
            with open(target_filepath, 'r', encoding='utf-8') as f:
                self.code = f.read()
            self.ast_tree = ast.parse(self.code)
        except Exception as e:
            print(f"Python AST Parsing Warning for {self.filename}: {e}")

    def audit_subprocess_calls(self):
        warnings = []
        if not self.ast_tree:
            return warnings

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        func_name = f"{node.func.value.id}.{node.func.attr}"
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                if func_name in ("subprocess.run", "subprocess.Popen", "os.system"):
                    # For os.system we just flag it as un-hideable easily in the same way
                    if func_name == "os.system":
                        warnings.append({
                            "line": node.lineno,
                            "issue": "OS_SYSTEM_POPUP: os.system used. Use subprocess with creationflags=0x08000000 instead to prevent Windows popup."
                        })
                        continue

                    # Check for creationflags kwargs
                    has_creationflags = False
                    for kw in node.keywords:
                        if kw.arg == "creationflags":
                            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int) and (kw.value.value & 0x08000000) != 0:
                                has_creationflags = True

                    if not has_creationflags:
                        warnings.append({
                            "line": node.lineno,
                            "issue": f"SUBPROCESS_POPUP: {func_name} called without creationflags=0x08000000 (CREATE_NO_WINDOW). This will cause a desktop console window flash."
                        })
        return warnings

    @staticmethod
    def detect_daemon_duplicates(script_name):
        """
        Uses psutil to detect if there are multiple instances of the same script running.
        Returns a list of duplicate PIDs.
        """
        duplicates = []
        current_pid = os.getpid()

        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = p.info.get('cmdline') or []
                if p.info['pid'] != current_pid and any(script_name in cmd for cmd in cmdline) and 'python' in p.info.get('name', '').lower():
                    duplicates.append(p.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        return duplicates
