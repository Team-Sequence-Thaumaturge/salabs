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
            if node.type == 'FunctionDeclaration' and node.id:
                declarations[node.id.name] = node.loc.start.line
            elif node.type == 'CallExpression' and node.callee.type == 'Identifier':
                usages.append({'name': node.callee.name, 'line': node.loc.start.line})

        self._traverse(self.ast, visitor)

        torsions = []
        for u in usages:
            name = u['name']
            if name in declarations:
                def_line = declarations[name]
                ref_line = u['line']
                if ref_line < def_line:
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
        def visitor(node):
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
            if self.language == 'python':
                import ast as pyast
                if isinstance(node, pyast.Name) and isinstance(node.ctx, pyast.Load):
                    usages.add(node.id)
                elif isinstance(node, pyast.arg): # function arguments
                    usages.add(node.arg)
                elif isinstance(node, pyast.FunctionDef):
                    usages.add(node.name)
                elif isinstance(node, pyast.ClassDef):
                    usages.add(node.name)
                elif isinstance(node, pyast.Call):
                    if isinstance(node.func, pyast.Name):
                        usages.add(node.func.id)
                    elif isinstance(node.func, pyast.Attribute):
                        usages.add(node.func.attr)
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
