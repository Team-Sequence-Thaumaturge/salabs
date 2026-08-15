import os
import hashlib
from .sapq_cascade_graph import SAPQCascadeGraph

class SAPQBaselineCube:
    """
    Phase 20: Hyper-Isomorphic Baseline Auditor (3D Tensor Cube)
    - Constructs Topological Roles based on AST capabilities (reads state, writes DOM, handles events).
    - Compares Baseline ☒' with Target ☒ to detect Topological Holes (MISSING_INTENDED_FEATURE).
    """
    def __init__(self, baseline_filepath, target_filepath=None, baseline_code=None, target_code=None):
        self.baseline_filepath = baseline_filepath
        self.target_filepath = target_filepath
        self.baseline_code = baseline_code
        self.target_code = target_code

        # Load Baseline Graph
        self.baseline_graph = SAPQCascadeGraph(filepath=self.baseline_filepath, code=self.baseline_code)

        # Load Target Graph
        if self.target_filepath or self.target_code:
            self.target_graph = SAPQCascadeGraph(filepath=self.target_filepath, code=self.target_code)
        else:
            self.target_graph = None

    def _generate_topological_hashes(self, graph):
        """
        Generates semantic hashes based on the *role* of functions, not their names.
        Role is defined by [Reads State] + [Writes DOM] + [Event Triggers].
        """
        # We need the functions dict from the cascade graph analysis
        # We'll re-run a lightweight traversal to grab the raw function capabilities
        functions = {}

        if not graph.ast:
            return set(), functions

        def traverse_ast(node, stack):
            if not node or not hasattr(node, 'type'): return

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
                    'is_event_handler': False,
                    'line': node.loc.start.line
                }
                stack.append(func_name)

            if stack:
                curr_func = stack[-1]
                func_info = functions[curr_func]

                # Check State Reads
                if node.type == 'Identifier' and any(kw in node.name.lower() for kw in ('state', 'context', 'data', 'store', 'model')):
                    if node.name != curr_func: func_info['reads_state'] = True

                # Check DOM Writes
                if node.type == 'AssignmentExpression' and getattr(node.left, 'type', '') == 'MemberExpression':
                    prop = node.left.property
                    if getattr(prop, 'type', '') == 'Identifier' and prop.name in ('innerHTML', 'textContent', 'value', 'display', 'className', 'style'):
                        func_info['writes_dom'] = True
                if node.type == 'CallExpression' and getattr(node.callee, 'type', '') == 'MemberExpression':
                    prop = node.callee.property
                    if getattr(prop, 'type', '') == 'Identifier' and prop.name in ('setAttribute', 'appendChild', 'remove', 'classList'):
                        func_info['writes_dom'] = True

                # Heuristic: Functions attached to events usually take 'event' or 'e' as args, or are named on* / handle*
                if curr_func.startswith('on') or curr_func.startswith('handle'):
                    func_info['is_event_handler'] = True

            for key, value in vars(node).items():
                if isinstance(value, list):
                    for item in value:
                        if hasattr(item, 'type'): traverse_ast(item, stack)
                elif hasattr(value, 'type'): traverse_ast(value, stack)

            if is_func: stack.pop()

        traverse_ast(graph.ast, [])

        # Generate Hash Matrix
        # E.g., A function that reads state and writes DOM is a "STATE_TO_DOM_MUTATOR"
        hashes = set()
        for name, info in functions.items():
            role_signature = f"READS_STATE:{info['reads_state']}|WRITES_DOM:{info['writes_dom']}|IS_HANDLER:{info['is_event_handler']}"
            # Only track meaningful topological nodes (ignore empty/dummy functions)
            if info['reads_state'] or info['writes_dom'] or info['is_event_handler']:
                # Using a string hash representation
                hashes.add(role_signature)

        return hashes, functions

    def audit_topological_holes(self):
        """
        Cross-audits Baseline vs Target to find MISSING_INTENDED_FEATURE.
        Returns a list of issues. If Target is missing, bypasses check safely.
        """
        issues = []
        if not self.baseline_graph or not self.target_graph:
            return issues # Graceful Bypass (Dual Mode missing Target)

        base_hashes, base_funcs = self._generate_topological_hashes(self.baseline_graph)
        targ_hashes, target_funcs = self._generate_topological_hashes(self.target_graph)

        # 1:1 Mapping: Find sets that existed in Baseline but vanished in Target
        missing_roles = base_hashes - targ_hashes

        for role in missing_roles:
            # Find the original function name for context
            orig_funcs = [name for name, info in base_funcs.items() if f"READS_STATE:{info['reads_state']}|WRITES_DOM:{info['writes_dom']}|IS_HANDLER:{info['is_event_handler']}" == role]

            orig_func_names = ", ".join(orig_funcs) if orig_funcs else "Unknown"

            issues.append({
                "type": "MISSING_INTENDED_FEATURE",
                "issue": f"MISSING_INTENDED_FEATURE: Topological Hole Detected. The intended semantic capability '{role}' (e.g., '{orig_func_names}' in baseline) is completely absent in the target code.",
                "role_signature": role,
                "original_functions": orig_funcs
            })

        return issues
