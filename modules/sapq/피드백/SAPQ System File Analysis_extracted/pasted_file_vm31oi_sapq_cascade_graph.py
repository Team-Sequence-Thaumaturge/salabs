import os
import re
import esprima

class SAPQCascadeGraph:
    """
    Phase 19: State Lifecycle & Cascade Mutation Graph
    1. Cascade Graph: Root state to Sub state propagation tracking.
    2. Blind Interceptor Detection: Forced DOM/sub-state writes without reading context.
    3. Temporal Lifecycle Lock: Data Race detection (rendering before init).
    """
    def __init__(self, filepath=None, code=None):
        self.filepath = filepath
        self.code = code
        self.ast = None

        if filepath and not code:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if filepath.endswith('.html'):
                    scripts = re.findall(r'<script(?:\s+(?!type=["\']application/ld\+json["\'])[^>]*)?>(.*?)</script>', content, re.DOTALL)
                    clean_scripts = [s for s in scripts if not s.strip().startswith('{')]
                    self.code = "\n".join(clean_scripts)
                else:
                    self.code = content
            except Exception:
                self.code = ""

        if self.code and self.code.strip():
            try:
                self.ast = esprima.parseScript(self.code, loc=True, tolerant=True)
            except Exception as e:
                pass # Silent fallback on minor syntax errors

    def analyze(self):
        issues = []
        if not self.ast:
            return issues

        global_calls = []
        functions = {}

        def traverse_ast(node, stack):
            if not node or not hasattr(node, 'type'):
                return

            is_func = node.type in ('FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression')

            if is_func:
                func_name = None
                if getattr(node, 'id', None) and node.id.type == 'Identifier':
                    func_name = node.id.name
                else:
                    func_name = f"anonymous_{node.loc.start.line}"

                functions[func_name] = {
                    'reads_state': False,
                    'writes_dom': False,
                    'line': node.loc.start.line
                }
                stack.append(func_name)

            elif node.type == 'CallExpression' and getattr(node.callee, 'type', '') == 'Identifier':
                called_func = node.callee.name
                if not stack:
                    global_calls.append({"name": called_func, "line": node.loc.start.line})

            if stack:
                curr_func = stack[-1]
                func_info = functions[curr_func]

                # Check for state reads
                if node.type == 'Identifier' and any(kw in node.name.lower() for kw in ('state', 'context', 'data', 'store', 'model')):
                    if node.name != curr_func:
                        func_info['reads_state'] = True

                # Check for DOM writes
                if node.type == 'AssignmentExpression' and getattr(node.left, 'type', '') == 'MemberExpression':
                    prop = node.left.property
                    if getattr(prop, 'type', '') == 'Identifier' and prop.name in ('innerHTML', 'textContent', 'value', 'display', 'className', 'style'):
                        func_info['writes_dom'] = True

                if node.type == 'CallExpression' and getattr(node.callee, 'type', '') == 'MemberExpression':
                    prop = node.callee.property
                    if getattr(prop, 'type', '') == 'Identifier' and prop.name in ('setAttribute', 'appendChild', 'remove', 'classList'):
                        func_info['writes_dom'] = True

            for key, value in vars(node).items():
                if isinstance(value, list):
                    for item in value:
                        if hasattr(item, 'type'):
                            traverse_ast(item, stack)
                elif hasattr(value, 'type'):
                    traverse_ast(value, stack)

            if is_func:
                stack.pop()

        traverse_ast(self.ast, [])

        # Phase 19.2: Blind Interceptor Detection
        for func_name, info in functions.items():
            if info['writes_dom'] and not info['reads_state']:
                issues.append({
                    "type": "BLIND_INTERCEPTOR",
                    "issue": f"BLIND_INTERCEPTOR: Function '{func_name}' at L{info['line']} forcefully mutates DOM/Sub-state without reading any Root State context.",
                    "line": info['line']
                })

        # Phase 19.3: Temporal Lifecycle Lock
        init_found = False
        for call in global_calls:
            name = call['name'].lower()
            if any(kw in name for kw in ('init', 'load', 'fetch', 'setup', 'boot')):
                init_found = True
            elif any(kw in name for kw in ('render', 'update', 'draw', 'paint', 'mount')):
                if not init_found:
                    issues.append({
                        "type": "TEMPORAL_LIFECYCLE_LOCK",
                        "issue": f"TEMPORAL_LIFECYCLE_LOCK: Data Race. Rendering function '{call['name']}' called at L{call['line']} before any initialization state is booted.",
                        "line": call['line']
                    })

        return issues
