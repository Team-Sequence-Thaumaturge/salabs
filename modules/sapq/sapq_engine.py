import os
import re
import sys
import json
import time

try:
    from .sapq_preflight import SAPQPreflightGuard
    from .sapq_checkpoint import CheckpointManager
    from .sapq_logger import SAPQLogger
    from .sapq_ast_parser import ASTParser
except (ImportError, ValueError):
    from sapq_preflight import SAPQPreflightGuard
    from sapq_checkpoint import CheckpointManager
    from sapq_logger import SAPQLogger
    from sapq_ast_parser import ASTParser

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
        pattern_def = re.compile(r'(?:function\s+([a-zA-Z0-9_$]+)|const\s+([a-zA-Z0-9_$]+)|let\s+([a-zA-Z0-9_$]+)|var\s+([a-zA-Z0-9_$]+)|def\s+([a-zA-Z0-9_$]+)|class\s+([a-zA-Z0-9_$]+))')
        pattern_id = re.compile(r'id=["\']([a-zA-Z0-9_$]+)["\']')
        for idx, line in enumerate(self.lines):
            match = pattern_def.search(line)
            if match:
                symbol = next(g for g in match.groups() if g is not None)
                tokens.append({"line": idx + 1, "symbol": symbol, "type": "FORWARD_DEF", "code_snippet": line.strip()[:80]})

            for id_match in pattern_id.finditer(line):
                symbol = id_match.group(1)
                tokens.append({"line": idx + 1, "symbol": symbol, "type": "DOM_ID_DEF", "code_snippet": line.strip()[:80]})
        return tokens

    def parse_phase_2_backward(self):
        tokens = []
        # Phase 2 Hotfix: Capture standalone identifiers (arguments, returns) safely without object properties (.foo)
        pattern_usage = re.compile(r'(?<![\w$.])([a-zA-Z_$][a-zA-Z0-9_$]*)(?![\w$])')
        pattern_onclick = re.compile(r'onclick\s*=\s*([\"\'])(.*?)\1')
        pattern_string_literal = re.compile(r'["\']([a-zA-Z0-9_$]+)["\']')

        reserved_keywords = {
            'if', 'for', 'while', 'switch', 'catch', 'function', 'return', 'const', 'let', 'var',
            'document', 'window', 'Math', 'console', 'true', 'false', 'null', 'undefined', 'new', 'class'
        }

        # We need to strip out function and variable declarations to avoid parsing a declaration as a usage.
        pattern_decl_strip = re.compile(r'(?:function|const|let|var|def|class)\s+([a-zA-Z0-9_$]+)')

        for idx in range(self.total_lines - 1, -1, -1):
            line = self.lines[idx]

            # Remove declarations from the line before parsing for usages
            clean_line = pattern_decl_strip.sub('', line)

            # Strip simple string literals from line to prevent capturing text inside strings as variables
            clean_line = re.sub(r'["\'](.*?)["\']', '""', clean_line)

            for match in pattern_usage.finditer(clean_line):
                symbol = match.group(1)
                if symbol not in reserved_keywords:
                    tokens.append({"line": idx + 1, "symbol": symbol, "type": "BACKWARD_REF", "code_snippet": line.strip()[:80]})

            for onclick_match in pattern_onclick.finditer(line):
                onclick_code = onclick_match.group(2)
                for string_literal_match in pattern_string_literal.finditer(onclick_code):
                    symbol = string_literal_match.group(1)
                    tokens.append({"line": idx + 1, "symbol": symbol, "type": "DOM_EVENT_TARGET_REF", "code_snippet": line.strip()[:80]})
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
        for idx in range(self.total_lines - 1, -1, -2):
            line = self.lines[idx]
            if 'addEventListener' in line or 'postMessage' in line or 'setTimeout' in line or 'setInterval' in line:
                tokens.append({"line": idx + 1, "type": "SKIP_BACKWARD_EVENT", "code_snippet": line.strip()[:80]})
        return tokens

    def execute_vector_end_trajectory_linking(self):
        v1_forward = self.parse_phase_1_forward()
        v2_backward = self.parse_phase_2_backward()
        v3_skip_forward = self.parse_phase_3_skip_forward()
        v4_skip_backward = self.parse_phase_4_skip_backward()

        forward_symbols = {t["symbol"]: t["line"] for t in v1_forward if t["type"] == "FORWARD_DEF"}
        # Include DOM_ID_DEF in forward symbols so document.getElementById doesn't flag them as zombies
        for t in v1_forward:
            if t["type"] == "DOM_ID_DEF":
                forward_symbols[t["symbol"]] = t["line"]
        backward_symbols = {t["symbol"]: t["line"] for t in v2_backward}

        discontinuities = []
        zombie_nodes = []
        closed_loops = []

        # SAPQ 3.5 Fusion: Bring in AST Context to cross-verify zombie nodes
        ast_parser = ASTParser(self.filepath)
        ast_usages = ast_parser.get_all_identifier_usages()
        scope_undeclared_symbols = ast_parser.detect_scope_undeclared_symbols()
        function_declarations = ast_parser.get_function_declarations()

        # Zombie Nodes
        for symbol, line_num in forward_symbols.items():
            # Check Regex Scanner first
            if symbol not in backward_symbols and not symbol.startswith('btn_') and len(symbol) > 3:
                # SAPQ 3.5 Fusion: Cross-verify against true AST usages to prevent 100% false positives
                if symbol not in ast_usages:
                    zombie_nodes.append({
                        "symbol": symbol,
                        "defined_line": line_num,
                        "issue": "GHOST_NODE (Defined in V1 forward pass, but never referenced in V2 backward pass OR AST)"
                    })

        # Discontinuity Lines (Torsion Crossings)
        for symbol, ref_line in backward_symbols.items():
            if symbol in forward_symbols:
                def_line = forward_symbols[symbol]
                # If reference is inside a function or event handler in HTML, skip static torsion warning
                if ref_line < def_line:
                    # P1 Fix: FunctionDeclaration hoisting false positive removal using AST
                    status = "UNVERIFIED"
                    if symbol in function_declarations:
                        status = "REFUTED" # Valid hoisting confirmed by AST Tri-State Judgment

                    ref_code = self.lines[ref_line - 1] if ref_line <= len(self.lines) else ""
                    # Check if reference is inside script function scope
                    if not ('document.getElementById' in ref_code and 'function' in self.full_content_raw):
                        discontinuities.append({
                            "symbol": symbol,
                            "def_line": def_line,
                            "ref_line": ref_line,
                            "issue": f"TORSION_CROSSING: Referenced at line {ref_line} before declaration at line {def_line}",
                            "status": status
                        })

        # Phase 18: EVENT_TARGET_MISMATCH check
        event_target_mismatches = []
        dom_ids = {t["symbol"] for t in v1_forward if t["type"] == "DOM_ID_DEF"}
        for t in v2_backward:
            if t["type"] == "DOM_EVENT_TARGET_REF":
                if t["symbol"] not in dom_ids:
                    # Target referenced in an event handler does not exist as an ID in the file
                    event_target_mismatches.append({
                        "symbol": t["symbol"],
                        "ref_line": t["line"],
                        "issue": f"EVENT_TARGET_MISMATCH: Target ID '{t['symbol']}' referenced in event handler at L{t['line']} does not exist in the DOM."
                    })

        # SAPQ ReferenceError Trap: Scope Undeclared Symbols
        scope_undeclared_symbols = ast_parser.detect_scope_undeclared_symbols()

        # Event Loop Closed Loop Anomalies
        event_lines = [t["line"] for t in v4_skip_backward]
        if len(event_lines) > 20:
            closed_loops.append({
                "count": len(event_lines),
                "issue": "HIGH_EVENT_DENSITY: High frequency event triggers detected across skip-backward trajectory"
            })

        score = max(0, 100 - (len(discontinuities) * 10 + len(zombie_nodes) * 2 + len(event_target_mismatches) * 20 + len(scope_undeclared_symbols) * 20))

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
            "event_target_mismatches": event_target_mismatches[:10],
            "scope_undeclared_symbols": scope_undeclared_symbols[:10],
            "closed_loop_warnings": closed_loops
        }

        return report

try:
    from .sapq_baseline_cube import SAPQBaselineCube
    from .sapq_llm_auditor import DualLLMAuditor
    from .sapq_interlock import SAPQInterlock
    from .sapq_anti_mockup import AntiMockupDepthEngine
    from .sapq_causality import CausalityContradictionEngine
    from .sapq_dom_relay import SAPQDOMRelay
    from .sapq_spatial_projector import SpatialProjector
except (ImportError, ValueError):
    from sapq_baseline_cube import SAPQBaselineCube
    from sapq_llm_auditor import DualLLMAuditor
    from sapq_interlock import SAPQInterlock
    from sapq_anti_mockup import AntiMockupDepthEngine
    from sapq_causality import CausalityContradictionEngine
    from sapq_dom_relay import SAPQDOMRelay
    from sapq_spatial_projector import SpatialProjector

try:
    from multi_vector_parser import MultiVectorCrossParsingAuditEngine
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from multi_vector_parser import MultiVectorCrossParsingAuditEngine

def audit_file(filepath, session_id=None, baseline_filepath=None, audit_only=False):
    checkpoint_mgr = CheckpointManager(filepath, session_id=session_id, audit_only=audit_only)
    logger = SAPQLogger(filepath, session_id=checkpoint_mgr.session_id, audit_only=audit_only)

    logger.log_session_start()

    # Attempt to load an existing checkpoint
    if not audit_only:
        if checkpoint_mgr.load_checkpoint():
            if checkpoint_mgr.state_data["global_status"] == "COMPLETED":
                return {"status": "SKIP", "message": f"{filepath} already completed in session {checkpoint_mgr.session_id}."}

            # Verify hash before updating status (which would overwrite it if update_hash=True)
            if not checkpoint_mgr.verify_hash():
                return {"status": "ERROR", "message": "File hash mismatch on resume. Checkpoint invalid."}

            checkpoint_mgr.update_status("RECOVERING", update_hash=False)
        else:
            checkpoint_mgr.create_backup()
            checkpoint_mgr.update_status("PENDING")

        checkpoint_mgr.update_status("ANALYZING")
    else:
        # Prevent checkpoint modification
        checkpoint_mgr.update_status = lambda *args, **kwargs: None
        checkpoint_mgr.create_backup = lambda *args, **kwargs: None
        checkpoint_mgr.add_pending_issue = lambda *args, **kwargs: None
        checkpoint_mgr.clear_pending_issues = lambda *args, **kwargs: None
        # Mock state data for read-only
        checkpoint_mgr.state_data = {"global_status": "AUDIT_ONLY_PENDING", "pending_issues": {}, "resolved_issues": []}

    # Phase 0: Pre-flight Syntax Guard
    preflight = SAPQPreflightGuard(filepath)
    is_syntax_valid, syntax_errors = preflight.run_preflight()

    logger.log_preflight_result(is_syntax_valid, syntax_errors)

    if not is_syntax_valid:
        checkpoint_mgr.update_status("FAILED")
        return {
            "target_file": os.path.basename(filepath),
            "audit_integrity_score": 0,
            "preflight_status": "FAILED",
            "syntax_errors": syntax_errors,
            "session_context": checkpoint_mgr.get_context_prompt()
        }

    # Proceed to Phase 1-4 analysis
    engine = MultiVectorCrossParsingAuditEngine(filepath)
    report = engine.execute_vector_end_trajectory_linking()

    report["semantic_contradictions"] = report.get("semantic_contradictions", [])
    report["async_timing_contradictions"] = report.get("async_timing_contradictions", [])
    report["intent_mismatches"] = report.get("intent_mismatches", [])


    # 6. Phase 20: Baseline Cube (if exists)
    if baseline_filepath and os.path.exists(baseline_filepath):
        cube = SAPQBaselineCube(baseline_filepath=baseline_filepath, target_filepath=filepath)
        topological_holes = cube.audit_topological_holes()
        if topological_holes:
            report["missing_intended_features"] = topological_holes

    # Run remaining detached engines
    # AntiMockupDepthEngine
    anti_mockup = AntiMockupDepthEngine(filepath)
    mockups = anti_mockup.audit_mockups()
    if mockups:
        report["mockup_hallucinations"] = mockups

    # CausalityContradictionEngine
    causality = CausalityContradictionEngine(filepath)
    causalities = causality.audit_causality()
    if causalities:
        report["causality_contradictions"] = causalities

    # DualLLMAuditor (Intent Audit)
    # We will simulate the intent audit just to include it in the report, without actual OpenAI keys
    llm_auditor = DualLLMAuditor()
    intent_result = llm_auditor.audit_intent("Simulate prompt", report, engine.full_content_raw if 'engine' in locals() and hasattr(engine, 'full_content_raw') else "")
    if intent_result and not intent_result.get("approved"):
        report["spec_mismatches"] = intent_result.get("issues", [])

    # SAPQDOMRelay Integration (Phase 22 E2E Dynamic Error Capturing)
    if filepath.endswith('.html'):
        dom_relay = SAPQDOMRelay(filepath)
        # Dispatch a simple body click to trigger potential load/CORS/JS errors
        result = dom_relay.dispatch_event_and_capture('body', 'click', 100)
        runtime_errors = []
        if result and result.get("success"):
            for msg in result.get("console_messages", []):
                if msg.get("type") in ("error", "warning"):
                    runtime_errors.append(f"CONSOLE_{msg.get('type').upper()}: {msg.get('text')}")
            for err in result.get("page_errors", []):
                runtime_errors.append(f"PAGE_ERROR: {err}")
        elif result and not result.get("success"):
            runtime_errors.append(f"RELAY_ERROR: {result.get('error')}")

        if runtime_errors:
            report["runtime_console_errors"] = runtime_errors

    # Recalculate score based on all unified detections
    deductions = 0
    deductions += len(report.get("discontinuities_detected", [])) * 10
    deductions += len(report.get("zombie_nodes_detected", [])) * 2
    deductions += len(report.get("event_target_mismatches", [])) * 20
    deductions += len(report.get("missing_intended_features", [])) * 30
    deductions += len(report.get("mockup_hallucinations", [])) * 15
    deductions += len(report.get("causality_contradictions", [])) * 15
    deductions += len(report.get("spec_mismatches", [])) * 25
    deductions += len(report.get("runtime_console_errors", [])) * 10

    report["audit_integrity_score"] = max(0, 100 - deductions)

    # SAPQInterlock validation (circuit breaker)
    interlock = SAPQInterlock()
    try:
        interlock.evaluate_audit_report(report, strict_mode=False) # run in non-strict mode to not exit early
    except Exception as e:
        report["interlock_status"] = str(e)
    else:
        report["interlock_status"] = "PASSED"

    # Recalculate total score integrating all submodules
    valid_discontinuities = [d for d in report.get("discontinuities_detected", []) if d.get("status") != "REFUTED"]
    total_penalty = (
        len(valid_discontinuities) * 10 +
        len(report.get("zombie_nodes_detected", [])) * 2 +
        len(report.get("event_target_mismatches", [])) * 20 +
        len(report.get("causality_contradictions", [])) * 15 +
        len(report.get("mockup_hallucinations", [])) * 25 +
        len(report.get("missing_intended_features", [])) * 30 +
        len(report.get("cascade_graph_issues", [])) * 15 +
        len(report.get("python_subprocess_issues", [])) * 25 +
        len(report.get("llm_audit_issues", [])) * 20 +
        len(report.get("scope_undeclared_symbols", [])) * 25 +
        len(report.get("semantic_contradictions", [])) * 5 +
        len(report.get("async_timing_contradictions", [])) * 15 +
        len(report.get("intent_mismatches", [])) * 20
    )
    report["audit_integrity_score"] = max(0, 100 - total_penalty)

    # Inject Preflight results into report
    report["preflight_status"] = "PASSED"
    report["session_context"] = checkpoint_mgr.get_context_prompt()

    logger.log_audit_completion(
        report.get("audit_integrity_score", 0),
        report.get("discontinuities_detected", []),
        report.get("zombie_nodes_detected", [])
    )

    # Clear old pending issues before adding new ones from this run
    checkpoint_mgr.clear_pending_issues()

    # Example logic: add pending issues to checkpoint
    for dis in report.get("discontinuities_detected", []):
        checkpoint_mgr.add_pending_issue(dis["issue"].split(":")[0], f"Symbol: {dis['symbol']}")
    for zom in report.get("zombie_nodes_detected", []):
        checkpoint_mgr.add_pending_issue(zom["issue"].split(" ")[0], f"Symbol: {zom['symbol']}")

    # If score is somewhat acceptable or issues are zero, you might move to COMPLETED (placeholder logic)
    if report["audit_integrity_score"] == 100:
        if not audit_only: checkpoint_mgr.update_status("COMPLETED")
    else:
        # Assuming the next step for an AI would be patching
        if not audit_only: checkpoint_mgr.update_status("PATCHING")

    # Integrate 3D Spatial Topology Projection (AIT Architecture Blueprint Phase)
    try:
        projector = SpatialProjector(filepath)
        report["spatial_topology"] = projector.generate_tensors()
    except Exception as e:
        report["spatial_topology_error"] = str(e)

    return report

def audit_directory(dirpath, audit_only=False):
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
                rep = audit_file(fp, audit_only=audit_only)
                if os.path.basename(fp) == 'index.html' and index_desyncs:
                    rep['index_desync_warnings'] = index_desyncs
                    rep['audit_integrity_score'] = max(0, rep['audit_integrity_score'] - len(index_desyncs) * 5)
                results.append(rep)

    return results
