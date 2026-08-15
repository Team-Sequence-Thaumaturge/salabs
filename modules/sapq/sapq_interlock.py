import sys
import logging
import json

class SAPQInterlock:
    """
    Phase 17.5: Build Block & Notification Interlock
    - Build Circuit Breaker: Blocks deployment if any contradictions or vulnerabilities are found.
    - Telegram Alert Dispatch: Dispatches a detailed trace log to a Telegram notification channel.
    """
    def __init__(self):
        self.logger = logging.getLogger("SAPQInterlock")
        logging.basicConfig(level=logging.INFO)

    def dispatch_telegram_alert(self, report):
        """
        Dispatch a detailed trace log of the failed audit to the Telegram notification channel immediately.
        (Mocked to prevent actual network calls during CI).
        """
        self.logger.warning("TELEGRAM ALERT DISPATCHED: Deployment blocked due to SAPQ violations.")
        # print(json.dumps(report, indent=2))
        return True

    def evaluate_audit_report(self, report, strict_mode=True):
        """
        Evaluates the combined audit report.
        If critical issues (Level 1-4 contradictions, popup vulnerabilities, active API probe failures)
        are found, it trips the circuit breaker and exits with code 1.
        """
        total_issues = 0
        issue_details = []

        if "discontinuities_detected" in report and report["discontinuities_detected"]:
            total_issues += len(report["discontinuities_detected"])
            issue_details.extend(report["discontinuities_detected"])

        if "zombie_nodes_detected" in report and report["zombie_nodes_detected"]:
             total_issues += len(report["zombie_nodes_detected"])
             issue_details.extend(report["zombie_nodes_detected"])

        if "mockup_hallucinations" in report and report["mockup_hallucinations"]:
            total_issues += len(report["mockup_hallucinations"])
            issue_details.extend(report["mockup_hallucinations"])

        if "causality_contradictions" in report and report["causality_contradictions"]:
             total_issues += len(report["causality_contradictions"])
             issue_details.extend(report["causality_contradictions"])

        if "spec_mismatches" in report and report["spec_mismatches"]:
             total_issues += len(report["spec_mismatches"])
             issue_details.extend(report["spec_mismatches"])

        if "daemon_duplications" in report and report["daemon_duplications"]:
             total_issues += len(report["daemon_duplications"])
             issue_details.extend(report["daemon_duplications"])

        if total_issues > 0 and strict_mode:
            self.logger.error(f"CIRCUIT BREAKER TRIPPED: Found {total_issues} critical SAPQ violations.")
            self.dispatch_telegram_alert({"total_issues": total_issues, "details": issue_details})
            raise RuntimeError(f"CIRCUIT BREAKER TRIPPED: {total_issues} SAPQ violations.")
        elif total_issues > 0:
            self.logger.warning(f"Warning: Found {total_issues} SAPQ violations, but strict_mode is off.")
            self.dispatch_telegram_alert({"total_issues": total_issues, "details": issue_details})
            return False
        else:
            self.logger.info("SAPQ Interlock Check Passed: 0 Violations. Deployment approved.")
            return True

if __name__ == "__main__":
    interlock = SAPQInterlock()
    mock_report = {
        "mockup_hallucinations": [{"issue": "Test mockup hallucination"}]
    }
    # Test tripping (will exit 1)
    # interlock.evaluate_audit_report(mock_report)
