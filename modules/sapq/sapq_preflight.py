import os
import re
import esprima
import ast

class SAPQPreflightGuard:
    """
    Phase 0: Pre-flight Syntax Guard
    - Checks basic syntax validity before deep semantic analysis (Phase 1-4).
    - Detects Block Re-declarations (const/let).
    - Detects Unbalanced Curly Braces.
    - Fails fast on SyntaxError.
    """
    def __init__(self, target_filepath):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        self.code = ""
        self.errors = []

        try:
            with open(target_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.full_content = f.read()

            if target_filepath.endswith('.html'):
                scripts = re.findall(r'<script(?:\s+(?!type=["\']application/ld\+json["\'])[^>]*)?>(.*?)</script>', self.full_content, re.DOTALL)
                clean_scripts = [s for s in scripts if not s.strip().startswith('{')]
                self.code = "\n".join(clean_scripts)
            else:
                self.code = self.full_content
        except Exception as e:
            self.errors.append({"type": "FILE_READ_ERROR", "message": str(e)})

    def _strip_comments_and_strings(self, code):
        """Helper to remove strings and comments to accurately count braces."""
        # Strip strings first so URLs in strings (like 'http://') don't get treated as comments
        code = re.sub(r'(["\'])(?:(?=(\\?))\2.)*?\1', '', code)
        code = re.sub(r'`(?:\\`|[^`])*`', '', code)

        # Strip Python specific comments and docstrings if applicable
        if self.filepath.endswith('.py'):
            code = re.sub(r'#.*', '', code)
            code = re.sub(r'\'\'\'[\s\S]*?\'\'\'', '', code)
            code = re.sub(r'\"\"\"[\s\S]*?\"\"\"', '', code)
        else:
            # Then strip C-style comments
            code = re.sub(r'//.*', '', code) # single line
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL) # block
        return code

    def check_curly_braces(self):
        clean_code = self._strip_comments_and_strings(self.code)
        open_count = clean_code.count('{')
        close_count = clean_code.count('}')
        if open_count != close_count:
            self.errors.append({
                "type": "UNBALANCED_BRACES",
                "message": f"Mismatched curly braces: {open_count} open '{{', {close_count} close '}}'"
            })
            return False
        return True

    def _check_python_syntax(self):
        try:
            ast.parse(self.code, filename=self.filepath)
        except SyntaxError as e:
            self.errors.append({
                "type": "SYNTAX_ERROR",
                "message": f"SyntaxError: {e.msg} at L{e.lineno}"
            })
            return False
        except Exception as e:
            self.errors.append({
                "type": "SYNTAX_ERROR",
                "message": f"Parse Error: {str(e)}"
            })
            return False
        return True

    def check_syntax_and_redeclarations(self):
        if not self.code.strip():
            return True # Nothing to parse

        if self.filepath.endswith('.py'):
            return self._check_python_syntax()

        if self.filepath.endswith(('.cpp', '.hpp', '.c', '.h', '.rs')):
            # Fallback for unsupported languages to avoid silent skipping, just brace check.
            return True

        # JS parsing
        try:
            # Tolerant parsing to try and get an AST even with minor errors,
            # but if it fails completely, it's a hard syntax error.
            parsed_ast = esprima.parseScript(self.code, loc=True, tolerant=True)

            # Since esprima python doesn't explicitly throw on all redeclarations in tolerant mode,
            # we check the errors list returned by esprima if we are using tolerant mode (not always exposed in python wrapper easily)
            # Actually, esprima-python throws on hard syntax errors like let/const redeclarations usually,
            # or returns them in `ast.errors` if `tolerant=True` is supported fully.
            if hasattr(parsed_ast, 'errors') and parsed_ast.errors:
                 for err in parsed_ast.errors:
                     if 'Identifier' in err.message and 'has already been declared' in err.message:
                         self.errors.append({
                             "type": "BLOCK_REDECLARATION",
                             "message": f"SyntaxError: {err.message} at L{err.lineNumber}"
                         })
                     else:
                         self.errors.append({
                             "type": "SYNTAX_ERROR",
                             "message": f"SyntaxError: {err.message} at L{err.lineNumber}"
                         })
                 if self.errors:
                     return False

        except Exception as e:
            msg = str(e)
            if 'has already been declared' in msg:
                self.errors.append({
                     "type": "BLOCK_REDECLARATION",
                     "message": f"SyntaxError: {msg}"
                })
            else:
                self.errors.append({
                    "type": "SYNTAX_ERROR",
                    "message": f"SyntaxError: {msg}"
                })
            return False

        return True

    def run_preflight(self):
        """Runs all preflight checks and returns (is_valid, errors_list)."""
        if self.errors: # if file read failed
            return False, self.errors

        is_brace_ok = self.check_curly_braces()
        is_syntax_ok = self.check_syntax_and_redeclarations()

        return len(self.errors) == 0, self.errors
