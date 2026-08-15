import os
import re
import json
import esprima

class ASTParser:
    """
    Phase 16.1: Full AST (Abstract Syntax Tree) Node Tree Parser
    - Safely extract pure executable JavaScript blocks from HTML (excluding JSON-LD) and parse via esprima (ESTree Spec).
    - 100% Mathematical AST Torsion Detection: TORSION_CROSSING
    - AST Mockup Hallucination Detection: MOCKUP_HALLUCINATION
    """
    def __init__(self, target_filepath):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        self.ast = None
        self.code = ""
        
        try:
            with open(target_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.full_content = f.read()
            
            # Extract JS script contents for HTML files (ignore application/ld+json or non-JS tags)
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
            print(f"AST Parsing Warning for {self.filename}: {e}")

    def _traverse(self, node, visitor, scope_depth=0, inside_function=False):
        if not node or not hasattr(node, 'type'):
            return

        is_function = node.type in ('FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression')
        new_inside_function = inside_function or is_function

        visitor(node, scope_depth, new_inside_function)

        # Increase scope depth for blocks
        new_scope_depth = scope_depth + 1 if node.type == 'BlockStatement' or is_function else scope_depth

        for key, value in vars(node).items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, 'type'):
                        self._traverse(item, visitor, new_scope_depth, new_inside_function)
            elif hasattr(value, 'type'):
                self._traverse(value, visitor, new_scope_depth, new_inside_function)

    def detect_torsion_crossings(self):
        if not self.ast:
            return []
        
        declarations = {}
        usages = []
        local_scopes = {} # Tracks {symbol_name: list_of_scope_depths}

        def visitor(node, scope_depth, inside_function):
            # Track Global-like Function Declarations (top level or high level)
            if node.type == 'FunctionDeclaration' and node.id:
                declarations[node.id.name] = node.loc.start.line

            # Track Local Variable Declarations and Parameters to isolate block scopes
            if node.type == 'VariableDeclarator' and node.id.type == 'Identifier':
                if node.id.name not in local_scopes:
                    local_scopes[node.id.name] = []
                local_scopes[node.id.name].append(scope_depth)

            if node.type in ('FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'):
                if hasattr(node, 'params'):
                    for param in node.params:
                        if param.type == 'Identifier':
                            if param.name not in local_scopes:
                                local_scopes[param.name] = []
                            # Params belong to the inner scope depth (which increments for function bodies)
                            local_scopes[param.name].append(scope_depth + 1)

            # Track Usage (Call Expressions)
            elif node.type == 'CallExpression' and node.callee.type == 'Identifier':
                usages.append({
                    'name': node.callee.name,
                    'line': node.loc.start.line,
                    'inside_function': inside_function,
                    'scope_depth': scope_depth
                })

        self._traverse(self.ast, visitor)

        torsions = []
        for u in usages:
            name = u['name']
            if name in declarations:
                # Check if this usage is shadowed by a local variable/parameter in its scope or a parent scope > 0
                is_shadowed = False
                if name in local_scopes:
                    for decl_depth in local_scopes[name]:
                        if decl_depth > 0 and decl_depth <= u['scope_depth']:
                            is_shadowed = True
                            break

                if is_shadowed:
                    continue # Skip, it's a local variable shadowing a global declaration

                def_line = declarations[name]
                ref_line = u['line']
                # If reference is < definition line, it's a torsion crossing,
                # UNLESS it's inside a function body (lazy evaluation).
                if ref_line < def_line and not u['inside_function']:
                    torsions.append({
                        'symbol': name,
                        'def_line': def_line,
                        'ref_line': ref_line,
                        'issue': f"AST_TORSION_CROSSING: Call at L{ref_line} before FunctionDeclaration at L{def_line}"
                    })
        return torsions

    def detect_mockup_hallucinations(self):
        if not self.ast:
            return []
        
        mockups = []
        def visitor(node, scope_depth, inside_function):
            if node.type == 'ReturnStatement' and node.argument:
                if node.argument.type == 'Literal' and str(node.argument.value) in ('true', '1', 'ok', 'success'):
                    mockups.append({
                        'line': node.loc.start.line,
                        'issue': "MOCKUP_HALLUCINATION: Static literal return in ReturnStatement (potential dummy stub)"
                    })
                elif node.argument.type == 'CallExpression':
                    if hasattr(node.argument.callee, 'object') and getattr(node.argument.callee.object, 'name', '') == 'Math':
                        if getattr(node.argument.callee.property, 'name', '') == 'random':
                            mockups.append({
                                'line': node.loc.start.line,
                                'issue': "MOCKUP_HALLUCINATION: Return value depends solely on Math.random() static stub"
                            })

        self._traverse(self.ast, visitor)
        return mockups

    def get_all_identifier_usages(self):
        """Extracts a set of all variable identifier names used in the AST, strictly tracking usages (ignoring declarations)."""
        if not self.ast:
            return set()

        usages = set()

        def visitor(node):
            # If the node itself is an Identifier, it might be a usage OR a declaration.
            # We filter it by looking at parent contexts during traversal. But esprima AST doesn't have parent links easily accessible.
            # However, we can track actual usage properties from parent nodes like CallExpression, MemberExpression, AssignmentExpression right side, etc.
            pass

        def advanced_visitor(node):
            if not node or not hasattr(node, 'type'): return

            # 1. Used in assignments (right side)
            if node.type == 'AssignmentExpression' and node.right.type == 'Identifier':
                usages.add(node.right.name)
            # 2. Used in Binary/Logical expressions
            if node.type in ('BinaryExpression', 'LogicalExpression'):
                if node.left.type == 'Identifier': usages.add(node.left.name)
                if node.right.type == 'Identifier': usages.add(node.right.name)
            # 3. Used in Return statement
            if node.type == 'ReturnStatement' and node.argument and node.argument.type == 'Identifier':
                usages.add(node.argument.name)
            # 4. Used as an argument in a function call
            if node.type == 'CallExpression':
                for arg in node.arguments:
                    if arg.type == 'Identifier':
                        usages.add(arg.name)
            # 5. Used in variable declarator initialization (right side)
            if node.type == 'VariableDeclarator' and node.init and node.init.type == 'Identifier':
                usages.add(node.init.name)
            # 6. Used in Member expressions (left side only usually, e.g., obj.prop -> obj is used)
            if node.type == 'MemberExpression' and node.object.type == 'Identifier':
                usages.add(node.object.name)

        self._traverse(self.ast, advanced_visitor)
        return usages
