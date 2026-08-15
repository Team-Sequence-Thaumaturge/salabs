import os
import re
import json
import esprima

class SpecMatcher:
    """
    Phase 17.3: Spec-to-Code Semantic Alignment Matcher
    - Parses JS/HTML code and compares variables/objects against raw task specifications.
    - Checks Variable Value Alignment and Spec-to-Code Integrity.
    """
    def __init__(self, target_filepath, specs=None):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        self.specs = specs or {}
        self.ast = None
        self.code = ""

        try:
            with open(target_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.full_content = f.read()

            if target_filepath.endswith('.html'):
                scripts = re.findall(r'<script(?:\s+(?!type=["\']application/ld\+json["\'])[^>]*)?>(.*?)</script>', self.full_content, re.DOTALL)
                clean_scripts = [s for s in scripts if not s.strip().startswith('{')]
                self.code = "\n".join(clean_scripts)
            else:
                self.code = self.full_content

            if self.code.strip():
                self.ast = esprima.parseScript(self.code, loc=True, tolerant=True)
        except Exception as e:
            self.ast = None
            print(f"Spec Matcher Parsing Warning for {self.filename}: {e}")

    def _traverse(self, node, visitor):
        if not node or not hasattr(node, 'type'):
            return
        visitor(node)
        for key, value in vars(node).items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, 'type'):
                        self._traverse(item, visitor)
            elif hasattr(value, 'type'):
                self._traverse(value, visitor)

    def audit_specs(self):
        """
        Compare actual AST ObjectExpression or AssignmentExpression nodes against self.specs.
        Returns a list of mismatches.
        """
        if not self.ast or not self.specs:
            return []

        mismatches = []
        found_keys = set()

        def visitor(node):
            # Check variable declarations: let x = 40;
            if node.type == 'VariableDeclarator' and node.id.type == 'Identifier' and node.init:
                key = node.id.name
                if key in self.specs:
                    found_keys.add(key)
                    if node.init.type == 'Literal':
                        val = node.init.value
                        if str(val) != str(self.specs[key]):
                            mismatches.append({
                                "type": "TORSION_CROSSING",
                                "line": node.loc.start.line,
                                "issue": f"SPEC_MISMATCH: Variable '{key}' has value '{val}' but spec requires '{self.specs[key]}'."
                            })

            # Check Object properties: { targetFrequency: 40 }
            if node.type == 'Property' and node.key.type == 'Identifier' and node.value:
                key = node.key.name
                if key in self.specs:
                    found_keys.add(key)
                    if node.value.type == 'Literal':
                        val = node.value.value
                        if str(val) != str(self.specs[key]):
                            mismatches.append({
                                "type": "TORSION_CROSSING",
                                "line": node.loc.start.line,
                                "issue": f"SPEC_MISMATCH: Object property '{key}' has value '{val}' but spec requires '{self.specs[key]}'."
                            })

            # Check assignments: obj.targetFrequency = 40;
            if node.type == 'AssignmentExpression' and node.left.type == 'MemberExpression' and node.left.property.type == 'Identifier':
                key = node.left.property.name
                if key in self.specs:
                    found_keys.add(key)
                    if node.right.type == 'Literal':
                        val = node.right.value
                        if str(val) != str(self.specs[key]):
                            mismatches.append({
                                "type": "TORSION_CROSSING",
                                "line": node.loc.start.line,
                                "issue": f"SPEC_MISMATCH: Assigned property '{key}' has value '{val}' but spec requires '{self.specs[key]}'."
                            })

        self._traverse(self.ast, visitor)

        # Check for missing specs completely
        for k, v in self.specs.items():
            if k not in found_keys:
                 mismatches.append({
                    "type": "TORSION_CROSSING",
                    "issue": f"SPEC_MISSING: Spec requirement '{k}' (value: '{v}') was not found in the AST."
                 })

        return mismatches

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "tools/jules-master-3d-spatial-engine-v1-2.html"
    specs = {"audioFrequency": 440, "gravity": 9.81}
    matcher = SpecMatcher(target, specs)
    issues = matcher.audit_specs()
    print(json.dumps(issues, indent=2))
