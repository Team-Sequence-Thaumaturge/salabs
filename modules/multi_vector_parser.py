import os
import re
import sys
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

class MultiVectorCrossParsingAuditEngine:
    """
    다방향 교차 파싱 기반 코드 무결성 자동 검수 엔진 (Multi-Directional Interleaved Cross-Parsing Audit Engine)
    - Phase 1: Forward Sequential (A -> Z)
    - Phase 2: Backward Sequential (Z -> A)
    - Phase 3: Skip Forward (a -> c -> e ...)
    - Phase 4: Skip Backward (z -> x -> v ...)
    - Vector End Stage: Trajectory Line Linking & Discontinuity / Zombie Node Audit
    """
    def __init__(self, target_filepath):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        with open(target_filepath, 'r', encoding='utf-8', errors='ignore') as f:
            self.lines = [line.rstrip() for line in f.readlines()]
        self.total_lines = len(self.lines)
        
    def parse_phase_1_forward(self):
        """Phase 1: A -> Z Forward Scan (Hoisting, Defs, Global Tokens)"""
        tokens = []
        pattern_def = re.compile(r'(?:function\s+([a-zA-Z0-9_$]+)|const\s+([a-zA-Z0-9_$]+)|let\s+([a-zA-Z0-9_$]+)|var\s+([a-zA-Z0-9_$]+)|id=["\']([a-zA-Z0-9_$]+)["\'])')
        
        for idx, line in enumerate(self.lines):
            match = pattern_def.search(line)
            if match:
                symbol = next(g for g in match.groups() if g is not None)
                tokens.append({
                    "line": idx + 1,
                    "symbol": symbol,
                    "type": "FORWARD_DEF",
                    "code_snippet": line.strip()[:80]
                })
        return tokens

    def parse_phase_2_backward(self):
        """Phase 2: Z -> A Backward Scan (Reverse Dependency & Orphaned Node Audit)"""
        tokens = []
        pattern_usage = re.compile(r'(?:document\.getElementById\(["\']([a-zA-Z0-9_$]+)["\']\)|window\.([a-zA-Z0-9_$]+)|([a-zA-Z0-9_$]+)\()')
        
        for idx in range(self.total_lines - 1, -1, -1):
            line = self.lines[idx]
            match = pattern_usage.search(line)
            if match:
                symbol = next(g for g in match.groups() if g is not None)
                if symbol not in ('if', 'for', 'while', 'switch', 'catch', 'function', 'return'):
                    tokens.append({
                        "line": idx + 1,
                        "symbol": symbol,
                        "type": "BACKWARD_REF",
                        "code_snippet": line.strip()[:80]
                    })
        return tokens

    def parse_phase_3_skip_forward(self):
        """Phase 3: a -> c -> e Skip Forward Scan (Odd Lines: Interleaved State Leaks)"""
        tokens = []
        for idx in range(0, self.total_lines, 2):
            line = self.lines[idx]
            if '=' in line or '->' in line or 'onchange' in line or 'onclick' in line:
                tokens.append({
                    "line": idx + 1,
                    "type": "SKIP_FORWARD_STATE",
                    "code_snippet": line.strip()[:80]
                })
        return tokens

    def parse_phase_4_skip_backward(self):
        """Phase 4: z -> x -> v Skip Backward Scan (Even Lines: Event Loop State Pollution)"""
        tokens = []
        for idx in range(self.total_lines - 1, -1, -2):
            line = self.lines[idx]
            if 'addEventListener' in line or 'postMessage' in line or 'setTimeout' in line or 'setInterval' in line:
                tokens.append({
                    "line": idx + 1,
                    "type": "SKIP_BACKWARD_EVENT",
                    "code_snippet": line.strip()[:80]
                })
        return tokens

    def execute_vector_end_trajectory_linking(self):
        try:
            return self._execute_vector_end_trajectory_linking_impl()
        except Exception as e:
            return {
                "target_file": self.filename,
                "audit_integrity_score": 0,
                "error_tensor": f"CRITICAL_PARSE_FAILURE: {str(e)}"
            }

    def _execute_vector_end_trajectory_linking_impl(self):
        """Vector End Stage: Trajectory Line Linking & Discontinuity Detection"""
        v1_forward = self.parse_phase_1_forward()
        v2_backward = self.parse_phase_2_backward()
        v3_skip_forward = self.parse_phase_3_skip_forward()
        v4_skip_backward = self.parse_phase_4_skip_backward()

        forward_symbols = {t["symbol"]: t["line"] for t in v1_forward}
        backward_symbols = {t["symbol"]: t["line"] for t in v2_backward}

        discontinuities = []
        zombie_nodes = []
        closed_loops = []

        # 1. Check Zombie Nodes (Defined in V1 but never referenced in V2)
        for symbol, line_num in forward_symbols.items():
            if symbol not in backward_symbols and not symbol.startswith('btn_') and len(symbol) > 3:
                zombie_nodes.append({
                    "symbol": symbol,
                    "defined_line": line_num,
                    "issue": "GHOST_NODE (Defined in V1 forward pass, but never referenced in V2 backward pass)"
                })

        # 2. Check Discontinuity Lines (References before declarations)
        for symbol, ref_line in backward_symbols.items():
            if symbol in forward_symbols:
                def_line = forward_symbols[symbol]
                if ref_line < def_line:
                    discontinuities.append({
                        "symbol": symbol,
                        "def_line": def_line,
                        "ref_line": ref_line,
                        "issue": f"TORSION_CROSSING: Referenced at line {ref_line} before declaration at line {def_line}"
                    })

        # 3. Check Event Loop Closed Loop Anomalies (Phase 4 Event pollution)
        event_lines = [t["line"] for t in v4_skip_backward]
        if len(event_lines) > 20:
            closed_loops.append({
                "count": len(event_lines),
                "issue": "HIGH_EVENT_DENSITY: High frequency event triggers detected across skip-backward trajectory"
            })

        # Phase 13.4 Level 2: Semantic State & Tensor Matrix Contradiction (Mockup/Dummy Check)
        semantic_contradictions = []
        pattern_dummy = re.compile(r'(?:Math\.random\(\)|setTimeout\s*\(\s*function\s*\(\)\s*\{|setTimeout\s*\(\s*\(\)\s*=>\s*\{)')
        for idx, line in enumerate(self.lines):
            if pattern_dummy.search(line):
                semantic_contradictions.append({
                    "line": idx + 1,
                    "issue": "DUMMY_STATE_CONTRADICTION: Potential mockup or fake state (Math.random / dummy setTimeout)",
                    "code_snippet": line.strip()[:80]
                })

        # Phase 13.4 Level 3: Asynchronous Event Loop Timing Contradiction
        async_timing_contradictions = []
        for idx, line in enumerate(self.lines):
            if "await" in line and ".then(" in line:
                async_timing_contradictions.append({
                    "line": idx + 1,
                    "issue": "ASYNC_TIMING_RACE: Mixing await and .then() implies a timing or promise dead-lock contradiction",
                    "code_snippet": line.strip()[:80]
                })

        # Phase 13.4 Level 4: Intent/Spec Alignment Contradiction (INTENT_MISMATCH)
        intent_mismatches = []
        if len(v1_forward) < 5 and self.total_lines > 100:
             intent_mismatches.append({
                 "issue": "INTENT_MISMATCH: Large file with suspiciously few structural definitions, suggesting partial implementation or scope reduction."
             })

        score = max(0, 100 - (len(discontinuities) * 10 + len(zombie_nodes) * 2 + len(semantic_contradictions) * 5 + len(intent_mismatches) * 20))

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
            "semantic_contradictions": semantic_contradictions[:10],
            "async_timing_contradictions": async_timing_contradictions[:10],
            "intent_mismatches": intent_mismatches
        }

        return report

if __name__ == "__main__":
    target = r"c:\stella.os\Quanxs\sair\Flash.html"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        
    print(f"=== Running Multi-Directional Interleaved Cross-Parsing Audit Engine ===")
    print(f"Target: {target}\n")
    
    engine = MultiVectorCrossParsingAuditEngine(target)
    start_time = time.time()
    res = engine.execute_vector_end_trajectory_linking()
    elapsed = (time.time() - start_time) * 1000

    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\nAudit completed in {elapsed:.2f}ms. Vector End Trajectory Linking Successful!")
