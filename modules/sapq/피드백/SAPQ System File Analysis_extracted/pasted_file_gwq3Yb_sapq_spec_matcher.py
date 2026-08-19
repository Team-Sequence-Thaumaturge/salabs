import re, os

class SpecSemanticMatcher:
    def __init__(self, raw_spec, target_filepath, code_content=None):
        self.raw_spec = raw_spec if isinstance(raw_spec, str) else ''
        self.filepath = target_filepath if isinstance(target_filepath, str) else ''
        if code_content is None and os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    self.code_content = f.read()
            except Exception:
                self.code_content = ''
        else:
            self.code_content = code_content or ''
        
        # If raw_spec is a dict (like in test_sapq.py test_spec_matcher_detects_torsion_crossing)
        if isinstance(raw_spec, dict):
            self.spec_variables = raw_spec
        else:
            self.spec_variables = self._extract_spec_variables()

    def _extract_spec_variables(self):
        variables = {}
        pattern = re.compile(r'([a-zA-Z0-9_\s]+)\s*=\s*([0-9]+(?:\.[0-9]+)?|[a-zA-Z0-9_]+)')
        for line in self.raw_spec.splitlines():
            match = pattern.search(line)
            if match:
                var_name = match.group(1).strip()
                val = match.group(2).strip()
                variables[var_name] = val
        return variables

    def audit_code_alignment(self):
        issues = []
        for var_name, spec_val in self.spec_variables.items():
            pattern = re.compile(rf'{var_name}\s*[:=]\s*([^\s,;]+)')
            match = pattern.search(self.code_content)
            if match:
                code_val = match.group(1).strip('\'"')
                if str(code_val).lower() != str(spec_val).lower():
                    issues.append({
                        "type": "SPEC_ALIGNMENT_MISMATCH",
                        "file": self.filepath,
                        "issue": f"SPEC_ALIGNMENT_MISMATCH: Spec required '{var_name} = {spec_val}', but code defined it as '{code_val}'."
                    })
            else:
                issues.append({
                    "type": "SPEC_ALIGNMENT_MISSING",
                    "file": self.filepath,
                    "issue": f"SPEC_ALIGNMENT_MISSING: Spec required '{var_name} = {spec_val}', but variable could not be found or mapped in code."
                })
        return issues

    def audit_specs(self):
        return self.audit_code_alignment()

SpecMatcher = SpecSemanticMatcher
SAPQSpecMatcher = SpecSemanticMatcher
