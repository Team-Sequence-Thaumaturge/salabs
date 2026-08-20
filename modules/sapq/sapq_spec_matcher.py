import re, os

class SpecMatcher:
    def __init__(self, arg1, arg2=None, code_content=None):
        if isinstance(arg1, str) and (isinstance(arg2, dict) or arg2 is None):
            self.filepath = arg1
            self.specs = arg2 or {}
            self.raw_spec = ""
        elif isinstance(arg1, (str, dict)) and isinstance(arg2, str):
            self.raw_spec = arg1
            self.filepath = arg2
            self.specs = arg1 if isinstance(arg1, dict) else {}
        else:
            self.filepath = str(arg1)
            self.specs = arg2 or {}
            self.raw_spec = ""

        if code_content is None and os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    self.code_content = f.read()
            except Exception:
                self.code_content = ""
        else:
            self.code_content = code_content or ""

    def audit_specs(self):
        issues = []
        target_dict = self.specs if isinstance(self.specs, dict) and self.specs else self._extract_spec_variables()
        for var_name, spec_val in target_dict.items():
            pattern = re.compile(rf'{var_name}\s*[:=]\s*([^\s,;]+)')
            match = pattern.search(self.code_content)
            if match:
                code_val = match.group(1).strip('\'"')
                if str(code_val).lower() != str(spec_val).lower():
                    issues.append({
                        "type": "SPEC_ALIGNMENT_MISMATCH",
                        "file": self.filepath,
                        "issue": f"SPEC_ALIGNMENT_MISMATCH: Mismatched spec {var_name} (expected {spec_val}, got {code_val})"
                    })
            else:
                issues.append({
                    "type": "GHOST_NODE",
                    "file": self.filepath,
                    "issue": f"SPEC_ALIGNMENT_MISSING / GHOST_NODE: Missing spec variable {var_name}"
                })
        return issues

    def audit_code_alignment(self):
        issues = self.audit_specs()
        for issue in issues:
            if issue["type"] == "TORSION_CROSSING":
                issue["type"] = "SPEC_ALIGNMENT_MISMATCH"
            elif issue["type"] == "GHOST_NODE":
                issue["type"] = "SPEC_ALIGNMENT_MISSING"
        return issues

    def _extract_spec_variables(self):
        variables = {}
        if isinstance(self.raw_spec, str):
            pattern = re.compile(r'([a-zA-Z0-9_\s]+)\s*=\s*([0-9]+(?:\.[0-9]+)?|[a-zA-Z0-9_]+)')
            for line in self.raw_spec.splitlines():
                match = pattern.search(line)
                if match:
                    var_name = match.group(1).strip()
                    val = match.group(2).strip()
                    variables[var_name] = val
        return variables

SpecSemanticMatcher = SpecMatcher
SAPQSpecMatcher = SpecMatcher
