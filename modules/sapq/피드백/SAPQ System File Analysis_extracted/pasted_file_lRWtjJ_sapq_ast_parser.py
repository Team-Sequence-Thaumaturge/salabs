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
            
            self.language = 'js'
            if target_filepath.endswith('.py'):
                self.language = 'python'
                self.code = self.full_content
                import ast as pyast
                if self.code.strip():
                    self.ast = pyast.parse(self.code)
            else:
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

    def _traverse(self, node, visitor):
        if self.language == 'python':
            import ast as pyast
            for subnode in pyast.walk(node):
                visitor(subnode)
            return

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

    def detect_torsion_crossings(self):
        if not self.ast:
            return []
        
        declarations = {}
        usages = []

        def visitor(node):
            if not hasattr(node, 'type'): return

            # Phase 1: Track const, let, var declarations (Block scope tracking)
            # We explicitly ignore FunctionDeclaration because JS functions are hoisted.
            if node.type == 'VariableDeclarator' and node.id and node.id.type == 'Identifier':
                declarations[node.id.name] = node.loc.start.line
            elif node.type == 'CallExpression' and node.callee.type == 'Identifier':
                usages.append({'name': node.callee.name, 'line': node.loc.start.line})
            elif node.type == 'Identifier':
                # Track general identifier usage for more accurate torsion crossing detection
                usages.append({'name': node.name, 'line': getattr(node.loc.start, 'line', 0)} if getattr(node, 'loc', None) else {'name': node.name, 'line': 0})

        if self.language != 'python':
            self._traverse(self.ast, visitor)

        if self.language == 'python':
            import ast as pyast
            class PythonTorsionVisitor(pyast.NodeVisitor):
                def visit_Assign(self, node):
                    for target in node.targets:
                        if isinstance(target, pyast.Name):
                            declarations[target.id] = getattr(node, 'lineno', 0)
                    self.generic_visit(node)
                def visit_Call(self, node):
                    if isinstance(node.func, pyast.Name):
                        usages.append({'name': node.func.id, 'line': getattr(node, 'lineno', 0)})
                    self.generic_visit(node)
                def visit_Name(self, node):
                    if isinstance(node.ctx, pyast.Load):
                        usages.append({'name': node.id, 'line': getattr(node, 'lineno', 0)})
            PythonTorsionVisitor().visit(self.ast)

        torsions = []
        for u in usages:
            name = u['name']
            if name in declarations:
                def_line = declarations[name]
                ref_line = u['line']
                # Local variables shadowing global, or hoisting exceptions: ensure ref_line is actually < def_line and > 0
                if 0 < ref_line < def_line:
                    torsions.append({
                        'symbol': name,
                        'def_line': def_line,
                        'ref_line': ref_line,
                        'issue': f"AST_TORSION_CROSSING: Call at L{ref_line} before declaration at L{def_line}"
                    })
        return torsions

    def detect_mockup_hallucinations(self):
        if not self.ast:
            return []
        
        mockups = []

        if self.language == 'python':
            import ast as pyast
            class PythonMockupVisitor(pyast.NodeVisitor):
                def visit_Return(self, node):
                    if isinstance(node.value, pyast.Constant):
                        if str(node.value.value) in ('True', '1', 'ok', 'success'):
                            mockups.append({
                                'line': getattr(node, 'lineno', 0),
                                'issue': "MOCKUP_HALLUCINATION: Static literal return in ReturnStatement (potential dummy stub)"
                            })
                    elif isinstance(node.value, pyast.Call):
                        # Detect random.random()
                        func = node.value.func
                        if isinstance(func, pyast.Attribute) and isinstance(func.value, pyast.Name):
                            if func.value.id == 'random' and func.attr == 'random':
                                mockups.append({
                                    'line': getattr(node, 'lineno', 0),
                                    'issue': "MOCKUP_HALLUCINATION: Return value depends solely on random.random() static stub"
                                })
                    self.generic_visit(node)
            PythonMockupVisitor().visit(self.ast)
            return mockups

        def visitor(node):
            if not hasattr(node, 'type'): return
            if node.type == 'ReturnStatement' and node.argument:
                if node.argument.type == 'Literal' and str(node.argument.value) in ('true', '1', 'ok', 'success'):
                    mockups.append({
                        'line': getattr(node.loc.start, 'line', 0) if getattr(node, 'loc', None) else 0,
                        'issue': "MOCKUP_HALLUCINATION: Static literal return in ReturnStatement (potential dummy stub)"
                    })
                elif node.argument.type == 'CallExpression':
                    if hasattr(node.argument.callee, 'object') and getattr(node.argument.callee.object, 'name', '') == 'Math':
                        if getattr(node.argument.callee.property, 'name', '') == 'random':
                            mockups.append({
                                'line': getattr(node.loc.start, 'line', 0) if getattr(node, 'loc', None) else 0,
                                'issue': "MOCKUP_HALLUCINATION: Return value depends solely on Math.random() static stub"
                            })

        self._traverse(self.ast, visitor)
        return mockups

    def extract_identifiers_from_pattern(self, pattern):
        ids = []
        if not pattern or not hasattr(pattern, 'type'): return ids
        if pattern.type == 'Identifier':
            ids.append(pattern.name)
        elif pattern.type == 'ArrayPattern':
            for elem in getattr(pattern, 'elements', []):
                if elem: ids.extend(self.extract_identifiers_from_pattern(elem))
        elif pattern.type == 'ObjectPattern':
            for prop in getattr(pattern, 'properties', []):
                if prop.type == 'Property' and getattr(prop, 'value', None):
                    ids.extend(self.extract_identifiers_from_pattern(prop.value))
                elif prop.type == 'RestElement':
                    ids.extend(self.extract_identifiers_from_pattern(prop.argument))
        elif pattern.type == 'RestElement':
            ids.extend(self.extract_identifiers_from_pattern(pattern.argument))
        elif pattern.type == 'AssignmentPattern':
            ids.extend(self.extract_identifiers_from_pattern(pattern.left))
        return ids

    def detect_scope_undeclared_symbols(self):
        if not self.ast or self.language != 'js':
            return []

        issues = []
        globals_builtins = {
            'window', 'document', 'console', 'Math', 'JSON', 'navigator',
            'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval',
            'alert', 'prompt', 'confirm', 'localStorage', 'sessionStorage',
            'location', 'history', 'fetch', 'XMLHttpRequest', 'require',
            'module', 'exports', 'process', 'global', '__dirname', '__filename',
            'Promise', 'Array', 'Object', 'String', 'Number', 'Boolean', 'RegExp',
            'Error', 'Date', 'Map', 'Set', 'WeakMap', 'WeakSet', 'Symbol',
            'isNaN', 'isFinite', 'parseFloat', 'parseInt', 'decodeURI', 'encodeURI',
            'decodeURIComponent', 'encodeURIComponent', 'eval', 'THREE',
            'undefined', 'arguments'
        }

        class Scope:
            def __init__(self, parent=None, scope_type='block'):
                self.parent = parent
                self.vars = set()
                self.scope_type = scope_type

            def declare(self, name, kind='let'):
                if kind == 'var' and self.scope_type == 'block' and self.parent:
                    self.parent.declare(name, kind)
                else:
                    self.vars.add(name)

            def is_declared(self, name):
                if name in self.vars: return True
                if self.parent: return self.parent.is_declared(name)
                return name in globals_builtins

        def get_all_hoisted_vars(node, is_root=False):
            hoisted = []
            if not node or not hasattr(node, 'type'): return hoisted

            # If we hit a nested function boundary, do not traverse into its body
            # because vars inside it belong to its scope, not ours.
            if not is_root and node.type in ('FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'):
                # However, for FunctionDeclaration, the function name ITSELF hoists to the current scope.
                if node.type == 'FunctionDeclaration' and getattr(node, 'id', None):
                    hoisted.append(node.id.name)
                return hoisted

            if node.type == 'VariableDeclaration' and node.kind == 'var':
                for decl in node.declarations:
                    if getattr(decl, 'id', None):
                        hoisted.extend(self.extract_identifiers_from_pattern(decl.id))

            for key, value in vars(node).items():
                if isinstance(value, list):
                    for item in value:
                        hoisted.extend(get_all_hoisted_vars(item, False))
                elif hasattr(value, 'type'):
                    hoisted.extend(get_all_hoisted_vars(value, False))
            return hoisted

        def collect_declarations(node, scope):
            if not node or not hasattr(node, 'type'): return
            if node.type == 'FunctionDeclaration' and getattr(node, 'id', None):
                pass # Hoisted
            elif node.type == 'VariableDeclaration':
                kind = node.kind
                # var has already been hoisted
                if kind != 'var':
                    for decl in node.declarations:
                        if getattr(decl, 'id', None):
                            for name in self.extract_identifiers_from_pattern(decl.id):
                                scope.declare(name, kind)
            elif node.type == 'ClassDeclaration' and getattr(node, 'id', None):
                scope.declare(node.id.name, 'let')
            elif node.type == 'ImportDeclaration':
                for specifier in getattr(node, 'specifiers', []):
                    if getattr(specifier, 'local', None):
                        scope.declare(specifier.local.name, 'const')

        def visit(node, scope):
            if not node or not hasattr(node, 'type'): return

            creates_scope = False
            scope_type = 'block'
            new_scope = scope

            if node.type in ('FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression', 'Program'):
                creates_scope = True
                scope_type = 'function'
            elif node.type in ('BlockStatement', 'ForStatement', 'ForInStatement', 'ForOfStatement', 'CatchClause', 'SwitchStatement'):
                creates_scope = True
                scope_type = 'block'

            if creates_scope:
                new_scope = Scope(parent=scope, scope_type=scope_type)
                if scope_type == 'function' or node.type == 'Program':
                    for hv in get_all_hoisted_vars(node, True):
                        new_scope.declare(hv, 'var')

                if node.type in ('FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'):
                    for param in getattr(node, 'params', []):
                        for name in self.extract_identifiers_from_pattern(param):
                            new_scope.declare(name, 'var')
                if node.type == 'CatchClause' and getattr(node, 'param', None):
                    for name in self.extract_identifiers_from_pattern(node.param):
                        new_scope.declare(name, 'let')

                body_list = []
                if node.type in ('Program', 'BlockStatement'):
                    body_list = getattr(node, 'body', [])
                elif node.type == 'SwitchStatement':
                    body_list = getattr(node, 'cases', [])
                if isinstance(body_list, list):
                    for stmt in body_list:
                        if getattr(stmt, 'type', None) == 'SwitchCase':
                            for sc_stmt in getattr(stmt, 'consequent', []):
                                collect_declarations(sc_stmt, new_scope)
                        else:
                            collect_declarations(stmt, new_scope)

                if node.type in ('ForStatement', 'ForInStatement', 'ForOfStatement'):
                    if getattr(node, 'init', None) and node.init.type == 'VariableDeclaration':
                        collect_declarations(node.init, new_scope)
                    if getattr(node, 'left', None) and node.left.type == 'VariableDeclaration':
                        collect_declarations(node.left, new_scope)

            def check_ident(n):
                if n and getattr(n, 'type', None) == 'Identifier' and not new_scope.is_declared(n.name):
                    line_num = getattr(n.loc.start, 'line', 0) if getattr(n, 'loc', None) and getattr(n.loc, 'start', None) else 0
                    issues.append({
                        'symbol': n.name,
                        'line': line_num,
                        'issue': f"SCOPE_UNDECLARED_SYMBOL: '{n.name}' is used but not declared (ReferenceError Trap)"
                    })

            # Check usages where identifiers appear explicitly!
            if node.type == 'Identifier':
                check_ident(node)

            # If a pattern has an assignment pattern with a default right side value, visit it
            if node.type == 'AssignmentPattern' and getattr(node, 'right', None):
                visit(node.right, new_scope)

            # Traverse children, but skip the properties we don't want to check as usage
            for key, value in vars(node).items():
                if key in ('id', 'params', 'param', 'label', 'imported', 'exported', 'local'):
                    if key in ('params', 'param', 'id'):
                        # Traverse inner properties that might be evaluated, like defaults in AssignmentPattern
                        if isinstance(value, list):
                            def visit_assignment_patterns(sub_node):
                                if not sub_node or not hasattr(sub_node, 'type'): return
                                if sub_node.type == 'AssignmentPattern' and getattr(sub_node, 'right', None):
                                    visit(sub_node.right, new_scope)
                                for k, v in vars(sub_node).items():
                                    if isinstance(v, list):
                                        for i in v: visit_assignment_patterns(i)
                                    elif hasattr(v, 'type'):
                                        visit_assignment_patterns(v)
                            for item in value:
                                visit_assignment_patterns(item)
                    continue # Skip declaration identifiers
                if node.type == 'MemberExpression' and key == 'property' and not getattr(node, 'computed', False):
                    continue # Skip non-computed properties
                if node.type == 'Property' and key == 'key' and not getattr(node, 'computed', False):
                    continue # Skip non-computed keys
                if node.type == 'MethodDefinition' and key == 'key' and not getattr(node, 'computed', False):
                    continue # Skip method names

                if isinstance(value, list):
                    for item in value:
                        visit(item, new_scope)
                elif hasattr(value, 'type'):
                    visit(value, new_scope)

        visit(self.ast, Scope(scope_type='function'))
        return issues

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
            if self.language == 'python':
                import ast as pyast
                if isinstance(node, pyast.Name) and isinstance(node.ctx, pyast.Load):
                    usages.add(node.id)
                elif isinstance(node, pyast.arg): # function arguments
                    usages.add(node.arg)
                return

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


# Backward compatibility alias
SAPQASTParser = ASTMultiVectorParser


# Backward compatibility aliases
ASTMultiVectorParser = ASTParser
SAPQASTParser = ASTParser
