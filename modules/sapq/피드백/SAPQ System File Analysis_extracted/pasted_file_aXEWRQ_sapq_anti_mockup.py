import re
import os

class AntiMockupDepthEngine:
    """
    Phase 15: Anti-Mockup, Hardcode Detection & Intent Coverage Depth Audit Engine
    - Flags fake crypto, dummy APIs, and hardcoded payment returns.
    - Audits MOCKUP_HALLUCINATION and SCOPE_REDUCTION.
    """
    def __init__(self, target_filepath):
        self.filepath = target_filepath
        self.filename = os.path.basename(target_filepath)
        try:
            with open(target_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.lines = [line.rstrip() for line in f.readlines()]
        except FileNotFoundError:
            self.lines = []

    def audit_mockups(self):
        """
        Scan for MOCKUP_HALLUCINATION and SCOPE_REDUCTION.
        """
        issues = []

        # 1. Fake Crypto / Signature Stubs
        pattern_fake_crypto = re.compile(r'(?:return\s+["\']mock_signature["\'])|(?:return\s+["\']eyJhbGciOiJIUzI1Ni["\'])|(?:Math\.random\(\).*signature)|(?:generateSignature.*\{\s*return\s+["\']0x)')

        for idx, line in enumerate(self.lines):
            if pattern_fake_crypto.search(line):
                issues.append({
                    "type": "MOCKUP_HALLUCINATION",
                    "subtype": "FAKE_CRYPTO",
                    "line": idx + 1,
                    "issue": "MOCKUP_HALLUCINATION (Fake Crypto): Hardcoded signature or Math.random() used instead of WebCrypto API.",
                    "code_snippet": line.strip()[:80]
                })

        # 2. Dummy API Stubs & Fake Delays
        pattern_dummy_api = re.compile(r'(?:setTimeout\s*\(\s*\(\)\s*=>\s*\{\s*resolve\()|(?:setTimeout\s*\(\s*function\(\)\s*\{\s*resolve\()')
        for idx, line in enumerate(self.lines):
            if pattern_dummy_api.search(line):
                issues.append({
                    "type": "MOCKUP_HALLUCINATION",
                    "subtype": "DUMMY_API",
                    "line": idx + 1,
                    "issue": "MOCKUP_HALLUCINATION (Dummy API): setTimeout with resolve() found, simulating a fake backend response.",
                    "code_snippet": line.strip()[:80]
                })

        # 3. Fake Payment / Settlement Returns
        pattern_fake_payment = re.compile(r'(?:function\s+processPayment.*\s*return\s+true;)|(?:const\s+status\s*=\s*["\']success["\'];\s*return\s+status;)')
        for idx, line in enumerate(self.lines):
            if pattern_fake_payment.search(line):
                issues.append({
                    "type": "MOCKUP_HALLUCINATION",
                    "subtype": "FAKE_PAYMENT",
                    "line": idx + 1,
                    "issue": "MOCKUP_HALLUCINATION (Fake Payment): Payment function returns a hardcoded 'true' or 'success' string without dynamic validation.",
                    "code_snippet": line.strip()[:80]
                })

        # 4. Scope Reduction Audit (Naïve line count vs expected endpoints - heuristic based)
        # If the file mentions multiple endpoints but has very few actual fetch calls
        endpoint_mentions = len([l for l in self.lines if "/api/v1/" in l or "Endpoint" in l])
        fetch_calls = len([l for l in self.lines if "fetch(" in l])

        if endpoint_mentions > 3 and fetch_calls < (endpoint_mentions / 2):
            issues.append({
                "type": "SCOPE_REDUCTION",
                "issue": f"SCOPE_REDUCTION: Mentions ~{endpoint_mentions} endpoints, but only implements ~{fetch_calls} active fetch calls. Suspicious AI scope reduction."
            })

        return issues

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "tools/jules-agentic-commerce-dashboard.html"
    engine = AntiMockupDepthEngine(target)
    issues = engine.audit_mockups()
    import json
    print(json.dumps(issues, indent=2))
