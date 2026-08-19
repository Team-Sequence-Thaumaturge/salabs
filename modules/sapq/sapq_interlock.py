import sys

class InterlockCircuitBreaker:
    """
    Phase 17.5: Build Block & Notification Interlock
    - Integrate upgraded SAPQ findings directly into the deployment workflow.
    - Build Circuit Breaker: If Level 1-4 contradictions, Python popup vulnerabilities, or active API probe failures are detected, block the deployment.
    - Telegram Alert Dispatch: Dispatch detailed trace log of failed audit.
    """

    class DeploymentBlocked(Exception):
        pass

    @staticmethod
    def evaluate_audit_report(report, strict_mode=True):
        """
        Evaluate a single audit report from SAPQ engine and decide whether to break the circuit.
        """
        return InterlockCircuitBreaker.evaluate_audit_results([report], strict_mode=strict_mode)

    @staticmethod
    def evaluate_audit_results(results, strict_mode=True):
        """
        Evaluate full audit results from SAPQ engines and decide whether to break the circuit.
        """
        has_critical_errors = False
        trace_log = []

        for res in results:
            # Check Level 1-4 contradictions
            valid_discontinuities = [d for d in res.get("discontinuities_detected", []) if d.get("status") != "REFUTED"]
            if valid_discontinuities or res.get("zombie_nodes_detected") or res.get("index_desync_warnings") or res.get("closed_loop_warnings") or res.get("scope_undeclared_symbols") or res.get("async_timing_contradictions") or res.get("semantic_contradictions") or res.get("intent_mismatches"):
                has_critical_errors = True
                trace_log.append(f"Level 1-4 Contradiction (or Scope Undeclared Symbols, Async Timing Race) found in {res.get('target_file')}")

            # Check Phase 15/16 (Mockup/Hallucination)
            if res.get("mockups_detected"):
                has_critical_errors = True
                trace_log.append(f"MOCKUP_HALLUCINATION found in {res.get('target_file')}")

            # Check Phase 17.1 (Python Popup vulnerabilities)
            if res.get("python_popup_warnings"):
                has_critical_errors = True
                trace_log.append(f"PYTHON_POPUP_VULNERABILITY found in {res.get('target_file')}")

            # Check Phase 17.2 (Active API Probe failures)
            if res.get("live_probe_failures"):
                has_critical_errors = True
                trace_log.append(f"LIVE_PROBE_FAILURE found in {res.get('target_file')}")

            # Check Phase 17.3 (Spec Alignment)
            if res.get("spec_alignment_warnings"):
                has_critical_errors = True
                trace_log.append(f"SPEC_ALIGNMENT_MISMATCH found in {res.get('target_file')}")

            if res.get("event_target_mismatches"):
                has_critical_errors = True
                trace_log.append(f"EVENT_TARGET_MISMATCH found in {res.get('target_file')}")

            if res.get("cascade_graph_issues"):
                has_critical_errors = True
                trace_log.append(f"CASCADE_GRAPH_ISSUE found in {res.get('target_file')}")

        if has_critical_errors:
            InterlockCircuitBreaker.dispatch_telegram_alert(trace_log)
            print("\n🚨 [CIRCUIT BREAKER TRIGGERED] Deployment blocked due to critical SAPQ audit failures:")
            for log in trace_log:
                print(f"  - {log}")
            if strict_mode:
                raise InterlockCircuitBreaker.DeploymentBlocked("SAPQ Deployment Audit Failed")
            return False
        else:
            print("✅ [CIRCUIT BREAKER] All checks passed. Deployment may proceed.")
            return True

    @staticmethod
    def dispatch_telegram_alert(trace_log):
        """
        Mock of Telegram Alert Dispatch.
        In a real scenario, this would use requests.post to the Telegram Bot API.
        """
        print("\n📲 [TELEGRAM ALERT MOCK] Dispatching trace log to Telegram channel...")
        message = "🚨 SAPQ Deployment Audit Failed! Trace Log:\n" + "\n".join([f"- {log}" for log in trace_log])
        # Example: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": message})
        print(message)
        print("📲 [TELEGRAM ALERT MOCK] Dispatch complete.\n")

SAPQInterlock = InterlockCircuitBreaker
SAPQInterlockEngine = InterlockCircuitBreaker


