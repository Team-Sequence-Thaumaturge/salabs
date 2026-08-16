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
