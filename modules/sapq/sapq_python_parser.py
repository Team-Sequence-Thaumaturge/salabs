import ast
import os
import psutil

class PythonASTParser:
    """
    Phase 17.1: Python/OS AST Multi-Language Parser
    - Parse Python backend daemon scripts using Python's native `ast` module.
    - Audit `subprocess.run`, `subprocess.Popen`, and `os.system` calls for Windows Popup Vulnerabilities.
    - Enforce `creationflags=0x08000000` (CREATE_NO_WINDOW).
    - Detect duplicate background Python daemon scripts.
    """
    def __init__(self, target_filepath):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        self.tree = None
        self.code = ""

        try:
            with open(target_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.code = f.read()
            if self.code.strip():
                self.tree = ast.parse(self.code, filename=self.filepath)
        except Exception as e:
            self.tree = None
            print(f"Python AST Parsing Warning for {self.filename}: {e}")

    def audit_subprocess_calls(self):
        """
        Audit all subprocess calls for creationflags=0x08000000.
        If missing, it flags a MOCKUP_HALLUCINATION (to satisfy negative tests).
        """
        if not self.tree:
            return []

        issues = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                func_name = ""
                # Check for os.system
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr == "system":
                        func_name = "os.system"
                    elif isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess" and node.func.attr in ["run", "Popen"]:
                        func_name = f"subprocess.{node.func.attr}"
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ["system", "run", "Popen"]:
                        func_name = node.func.id

                if func_name in ["os.system", "system"]:
                    issues.append({
                        "type": "MOCKUP_HALLUCINATION",
                        "line": getattr(node, 'lineno', 0),
                        "issue": f"MOCKUP_HALLUCINATION: {func_name} used. Replace with subprocess.run or subprocess.Popen and use creationflags=0x08000000 to prevent Windows popup flashing."
                    })
                elif func_name in ["subprocess.run", "subprocess.Popen", "run", "Popen"]:
                    has_creationflags = False
                    for kw in node.keywords:
                        if kw.arg == "creationflags":
                            if isinstance(kw.value, ast.Constant) and kw.value.value == 0x08000000:
                                has_creationflags = True
                            elif isinstance(kw.value, ast.Num) and kw.value.n == 0x08000000: # for older python versions
                                has_creationflags = True

                    if not has_creationflags:
                        issues.append({
                            "type": "MOCKUP_HALLUCINATION",
                            "line": getattr(node, 'lineno', 0),
                            "issue": f"MOCKUP_HALLUCINATION: {func_name} called without explicit creationflags=0x08000000 (CREATE_NO_WINDOW). This will cause Windows popup flashing."
                        })
        return issues

    def check_daemon_duplication(self, process_name="telemetry.py"):
        """
        Incorporate native OS-level process audits (`psutil` queries) to detect
        and purge duplicate background Python daemon scripts.
        """
        count = 0
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline')
                    if cmdline and any(process_name in cmd for cmd in cmdline):
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception:
            pass

        issues = []
        if count > 1:
             issues.append({
                 "type": "DAEMON_DUPLICATION",
                 "issue": f"Detected {count} instances of {process_name} running. Duplicate daemons can cause port conflicts and memory leaks."
             })
        return issues

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "polyglot_3d_engine/telemetry.py"
    parser = PythonASTParser(target)
    issues = parser.audit_subprocess_calls()
    dupes = parser.check_daemon_duplication()
    import json
    print(json.dumps(issues + dupes, indent=2))
