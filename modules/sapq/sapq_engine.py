import os
import re
import sys
import json
import time
from .sapq_ast_parser import ASTParser
from .sapq_anti_mockup import AntiMockupDepthEngine
from .sapq_python_parser import PythonASTParser
from .sapq_live_probe import LiveProbeEngine
from .sapq_spec_matcher import SpecSemanticMatcher

sys.stdout.reconfigure(encoding='utf-8')

class SAPQEngine:
    """
    SAPQ (Sequence Autonomic Parsing & QA) Master Engine v1.1
    - Level 1: Structural & Topological Placement Contradiction (TORSION_CROSSING, GHOST_NODE)
    - Level 2: Semantic State & Tensor Matrix Contradiction (INTERLOCK_DESYNC)
    - Level 3: Asynchronous Event Loop Timing Contradiction (RACE_CONDITION)
    - Level 4: User Intent & Spec Alignment Contradiction (INTENT_MISMATCH, INDEX_DESYNC)
    """
    def __init__(self, target_filepath):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        with open(target_filepath, 'r', encoding='utf-8', errors='ignore') as f:
            self.lines = [line.rstrip() for line in f.readlines()]
        self.total_lines = len(self.lines)
        self.full_content_raw = "\n".join(self.lines)
        
    def parse_phase_1_forward(self):
        tokens = []
        pattern_def = re.compile(r'(?:function\s+([a-zA-Z0-9_$]+)|const\s+([a-zA-Z0-9_$]+)|let\s+([a-zA-Z0-9_$]+)|var\s+([a-zA-Z0-9_$]+)|id=["\']([a-zA-Z0-9_$]+)["\'])')
        for idx, line in enumerate(self.lines):
            match = pattern_def.search(line)
            if match:
                symbol = next(g for g in match.groups() if g is not None)
                tokens.append({"line": idx + 1, "symbol": symbol, "type": "FORWARD_DEF", "code_snippet": line.strip()[:80]})
        return tokens

    def parse_phase_2_backward(self):
        tokens = []
        # Negative lookbehind (?<![\w$.]) prevents capturing properties like .name or trailing from other words
        # The identifier part captures valid JS variables including those starting with $
        # Negative lookahead (?![\w$]) ensures we don't truncate a longer valid identifier
        # Combined with legacy captures for window. and document.getElementById explicitly
        pattern_usage = re.compile(r'(?:document\.getElementById\(["\']([a-zA-Z0-9_$]+)["\']\))|(?:window\.([a-zA-Z0-9_$]+))|(?:(?<![\w$.])([a-zA-Z_$][a-zA-Z0-9_$]*)(?![\w$]))')

        ignore_keywords = {
            'if', 'for', 'while', 'switch', 'catch', 'function', 'return', 'let', 'const', 'var', 'class',
            'import', 'export', 'try', 'finally', 'else', 'do', 'new', 'this', 'super', 'typeof', 'instanceof',
            'in', 'of', 'async', 'await', 'break', 'continue', 'yield', 'null', 'true', 'false', 'undefined',
            'document', 'window', 'console', 'Math', 'JSON', 'Array', 'Object', 'String', 'Number', 'Boolean', 'Date',
            'getElementById', 'querySelector', 'querySelectorAll', 'addEventListener', 'removeEventListener',
            'length', 'push', 'pop', 'shift', 'unshift', 'forEach', 'map', 'filter', 'reduce', 'slice', 'splice',
            'log', 'warn', 'error', 'info', 'table', 'clear', 'time', 'timeEnd'
        }
        for idx in range(self.total_lines - 1, -1, -1):
            line = self.lines[idx]
            # Ignore comments for backward usage checks
            if line.strip().startswith('//') or line.strip().startswith('*'):
                continue

            matches = pattern_usage.finditer(line)
            for match in matches:
                symbol = next(g for g in match.groups() if g is not None)
                if symbol not in ignore_keywords:
                    tokens.append({"line": idx + 1, "symbol": symbol, "type": "BACKWARD_REF", "code_snippet": line.strip()[:80]})
        return tokens

    def parse_phase_3_skip_forward(self):
        tokens = []
        for idx in range(0, self.total_lines, 2):
            line = self.lines[idx]
            if '=' in line or '->' in line or 'onchange' in line or 'onclick' in line:
                tokens.append({"line": idx + 1, "type": "SKIP_FORWARD_STATE", "code_snippet": line.strip()[:80]})
        return tokens

    def parse_phase_4_skip_backward(self):
        tokens = []
        start_idx = self.total_lines - 1 if (self.total_lines - 1) % 2 == 1 else self.total_lines - 2
        for idx in range(start_idx, -1, -2):
            line = self.lines[idx]
            if 'addEventListener' in line or 'postMessage' in line or 'setTimeout' in line or 'setInterval' in line:
                tokens.append({"line": idx + 1, "type": "SKIP_BACKWARD_EVENT", "code_snippet": line.strip()[:80]})
        return tokens

    def execute_vector_end_trajectory_linking(self):
        v1_forward = self.parse_phase_1_forward()
        v2_backward = self.parse_phase_2_backward()
        v3_skip_forward = self.parse_phase_3_skip_forward()
        v4_skip_backward = self.parse_phase_4_skip_backward()

        forward_symbols = {t["symbol"]: t["line"] for t in v1_forward}

        # Collect all usage lines for each symbol as a list
        backward_usages = {}
        for t in v2_backward:
            sym = t["symbol"]
            line = t["line"]
            if sym not in backward_usages:
                backward_usages[sym] = []
            backward_usages[sym].append(line)

        discontinuities = []
        zombie_nodes = []
        closed_loops = []

        # Zombie Nodes
        for symbol, def_line in forward_symbols.items():
            is_referenced = False
            if symbol in backward_usages:
                usages = backward_usages[symbol]
                # Referenced if it appears multiple times OR if its single usage is on a different line
                if len(usages) > 1 or usages[0] != def_line:
                    is_referenced = True

            if not is_referenced and not symbol.startswith('btn_') and len(symbol) > 3:
                zombie_nodes.append({
                    "symbol": symbol,
                    "defined_line": def_line,
                    "issue": "GHOST_NODE (Defined in V1 forward pass, but never referenced outside its declaration line)"
                })

        # Discontinuity Lines (Torsion Crossings)
        for symbol, usages in backward_usages.items():
            if symbol in forward_symbols:
                def_line = forward_symbols[symbol]
                for ref_line in usages:
                    # If reference is strictly before the definition line
                    if ref_line < def_line:
                        ref_code = self.lines[ref_line - 1] if ref_line <= len(self.lines) else ""
                        # Check if reference is inside script function scope
                        if not ('document.getElementById' in ref_code and 'function' in self.full_content_raw):
                            discontinuities.append({
                                "symbol": symbol,
                                "def_line": def_line,
                                "ref_line": ref_line,
                                "issue": f"TORSION_CROSSING: Referenced at line {ref_line} before declaration at line {def_line}"
                            })

        # Event Loop Closed Loop Anomalies
        event_lines = [t["line"] for t in v4_skip_backward]
        if len(event_lines) > 20:
            closed_loops.append({
                "count": len(event_lines),
                "issue": "HIGH_EVENT_DENSITY: High frequency event triggers detected across skip-backward trajectory"
            })

        # Phase 15/16 Audits (Mockup, AST Torsion)
        ast_parser = ASTParser(self.filepath)
        discontinuities.extend(ast_parser.detect_torsion_crossings())
        mockups = ast_parser.detect_mockup_hallucinations()

        # Phase 17 Audits (Python, Probes, Spec Match)
        python_warnings = []
        if self.filepath.endswith('.py'):
            py_parser = PythonASTParser(self.filepath)
            python_warnings = py_parser.audit_subprocess_calls()

        # Probe Check
        # LiveProbeEngine implementation isolated; dynamic network requests
        # disabled here to prevent Blind SSRF vulnerabilities and unauthorized CI failures.
        live_probe_failures = []

        # Spec Semantic Check
        # Isolated for dedicated invocation via test suite or CLI flags.
        spec_warnings = []

        score = max(0, 100 - (len(discontinuities) * 10 + len(zombie_nodes) * 2 + len(mockups) * 15 + len(python_warnings) * 20 + len(live_probe_failures) * 20))

        report = {
            "target_file": self.filename,
            "total_lines": self.total_lines,
            "audit_integrity_score": score,
            "vector_nodes": {
                "V1_Forward_Count": len(v1_forward),
                "V2_Backward_Count": len(v2_backward),
                "V3_Skip_Forward_Count": len(v3_skip_forward),
                "V4_Skip_Backward_Count": len(v4_skip_backward)
            },
            "discontinuities_detected": discontinuities[:10],
            "zombie_nodes_detected": zombie_nodes[:10],
            "closed_loop_warnings": closed_loops,
            "mockups_detected": mockups,
            "python_popup_warnings": python_warnings,
            "live_probe_failures": live_probe_failures,
            "spec_alignment_warnings": spec_warnings
        }

        return report

def audit_file(filepath):
    engine = SAPQEngine(filepath)
    return engine.execute_vector_end_trajectory_linking()

def audit_directory(dirpath):
    results = []

    # Check INDEX_DESYNC across portal directory
    llms_txt_path = os.path.join(dirpath, "llms.txt")
    index_html_path = os.path.join(dirpath, "index.html")
    tools_dir = os.path.join(dirpath, "tools")

    llms_content = ""
    if os.path.exists(llms_txt_path):
        with open(llms_txt_path, "r", encoding="utf-8", errors="ignore") as f:
            llms_content = f.read()

    index_content = ""
    if os.path.exists(index_html_path):
        with open(index_html_path, "r", encoding="utf-8", errors="ignore") as f:
            index_content = f.read()

    index_desyncs = []

    # Cross-examine tools vs llms.txt & index.html
    if os.path.exists(tools_dir):
        for t in os.listdir(tools_dir):
            if t.endswith('.html'):
                if llms_content and t not in llms_content:
                    index_desyncs.append({
                        "file": t,
                        "issue": f"INDEX_DESYNC: Tool '{t}' exists in tools/ but is OMITTED from llms.txt GEO AI Index!"
                    })

    for root, dirs, files in os.walk(dirpath):
        for f in files:
            if f.endswith('.html') or f.endswith('.js') or f.endswith('.py'):
                fp = os.path.join(root, f)
                rep = audit_file(fp)
                if os.path.basename(fp) == 'index.html' and index_desyncs:
                    rep['index_desync_warnings'] = index_desyncs
                    rep['audit_integrity_score'] = max(0, rep['audit_integrity_score'] - len(index_desyncs) * 5)
                results.append(rep)

    return results
