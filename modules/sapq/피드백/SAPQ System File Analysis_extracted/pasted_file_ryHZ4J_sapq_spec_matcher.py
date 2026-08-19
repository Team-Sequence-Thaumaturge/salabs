import re

class SpecSemanticMatcher:
    """
    Phase 17.3: Spec-to-Code Semantic Alignment Matcher
    - Semantic validator that checks code's actual variables against raw task specifications.
    - Variable Value Alignment: Compare raw requirements variables against JS/HTML or Python parameters.
    """
    def __init__(self, raw_spec, target_filepath, code_content):
        self.raw_spec = raw_spec
        self.filepath = target_filepath
        self.code_content = code_content
        self.spec_variables = self._extract_spec_variables()

    def _extract_spec_variables(self):
        """
        Naive extraction of target variables from raw spec.
        Matches patterns like: "target frequency = 40" or "target_frequency = 40"
        """
        variables = {}
        # Simple regex to find "variable_name = value" or "variable name = value"
        # and capture the number or string
        pattern = re.compile(r'([a-zA-Z0-9_\s]+)\s*=\s*([0-9]+(?:\.[0-9]+)?|[a-zA-Z0-9_]+)')
        for line in self.raw_spec.splitlines():
            match = pattern.search(line)
            if match:
                var_name = match.group(1).strip()
                val = match.group(2).strip()
                variables[var_name] = val
        return variables

    def audit_code_alignment(self):
        warnings = []
        # Fallback simplistic regex to find variable assignment in the code
        for spec_var, spec_val in self.spec_variables.items():
            # Convert spaces to underscores for potential code variable names
            code_var_name = spec_var.replace(" ", "_")
            code_var_camel = "".join(x.capitalize() or '_' for x in code_var_name.split('_'))
            code_var_camel = code_var_camel[0].lower() + code_var_camel[1:] if code_var_camel else code_var_camel

            # Look for these variable names in the code content
            pattern = re.compile(rf'(?:{code_var_name}|{code_var_camel})\s*[:=]\s*([0-9]+(?:\.[0-9]+)?|[\'"]?[a-zA-Z0-9_]+[\'"]?)')
            match = pattern.search(self.code_content)

            if match:
                code_val = match.group(1).strip("'\"")
                if code_val != spec_val:
                    warnings.append({
                        "type": "SPEC_ALIGNMENT_MISMATCH",
                        "issue": f"SPEC_ALIGNMENT_MISMATCH: Spec required '{spec_var} = {spec_val}', but code defined it as '{code_val}'."
                    })
            else:
                warnings.append({
                    "type": "SPEC_ALIGNMENT_MISSING",
                    "issue": f"SPEC_ALIGNMENT_MISSING: Spec required '{spec_var} = {spec_val}', but variable could not be found or mapped in code."
                })

        return warnings
