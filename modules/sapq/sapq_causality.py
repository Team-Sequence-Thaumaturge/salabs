import re
import os

class CausalityContradictionEngine:
    """
    Phase 14: Systemic Causality & Inter-Site Flow Dependency Contradiction Engine
    - Tracks causal chains across modules/sites.
    - Audits Causal Breaks, Inversions, and Contradictions (CAUSALITY_CONTRADICTION).
    """
    def __init__(self, target_filepath):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        try:
            with open(target_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.full_content = f.read()
                f.seek(0)
                self.lines = [line.rstrip() for line in f.readlines()]
        except FileNotFoundError:
            self.full_content = ""
            self.lines = []

    def audit_causality(self):
        """
        Scan for systemic causality contradictions.
        Returns a list of identified CAUSALITY_CONTRADICTION issues.
        """
        contradictions = []

        # 1. Causal Break Detection (Triggered upstream but downstream effect is missing)
        # E.g., Payment triggered but no settlement logic found
        has_payment_trigger = any("processPayment" in line or "L402" in line for line in self.lines)
        has_settlement_effect = any("finalizeSettlement" in line or "crypto.subtle" in line for line in self.lines)

        if has_payment_trigger and not has_settlement_effect:
            contradictions.append({
                "type": "CAUSAL_BREAK",
                "issue": "CAUSALITY_CONTRADICTION: Trigger A (Payment/L402) found, but downstream Effect C (Settlement/WebCrypto) is completely missing."
            })

        # 2. Causal Inversion Detection (Effect is present without the necessary Trigger)
        # E.g., Rendering Topology Graph without initializing the Cognitive Core Data
        has_topology_render = any("renderTopology" in line or "drawNodes" in line for line in self.lines)
        has_core_init = any("initCognitionCore" in line or "fetchGlobalState" in line for line in self.lines)

        if has_topology_render and not has_core_init:
            contradictions.append({
                "type": "CAUSAL_INVERSION",
                "issue": "CAUSALITY_CONTRADICTION: Downstream Effect C (Topology Render) active without Upstream Trigger A (Cognition Core Init)."
            })

        # 3. Direct State/Intent Contradiction (Mismatched schema)
        # Look for conflicting state declarations or invalid state mutations that violate systemic causality
        pattern_contradict = re.compile(r'(?:state\.active\s*=\s*true;.*?disabled\s*=\s*true)|(?:disabled\s*=\s*true;.*?state\.active\s*=\s*true)', re.DOTALL)
        if pattern_contradict.search(self.full_content):
            contradictions.append({
                "type": "CAUSAL_CONTRADICTION",
                "issue": "CAUSALITY_CONTRADICTION: Upstream Cause and Downstream Effect conflict in state/intent (e.g. active vs disabled)."
            })

        return contradictions

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "tools/jules-master-3d-spatial-engine-v1-2.html"
    engine = CausalityContradictionEngine(target)
    issues = engine.audit_causality()
    import json
    print(json.dumps(issues, indent=2))
