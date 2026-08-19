import sys
import os
import json
import argparse
from .sapq_engine import SAPQEngine, audit_file, audit_directory
from .sapq_arbiter import SAPQArbiter

def main():
    parser = argparse.ArgumentParser(description="SAPQ - Sequence Autonomic Parsing & QA CLI Engine")
    parser.add_argument("target", help="Target file or directory path to audit")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")
    parser.add_argument("--baseline", type=str, help="Baseline original file for Phase 20 Hyper-Isomorphic auditing")
    parser.add_argument("--interrogate", action="store_true", help="Phase 21: Generate LLM Interrogation Dossier if holes exist")
    parser.add_argument("--audit-only", action="store_true", help="Phase 3: Run in non-destructive Audit Mode")
    args = parser.parse_args()

    target = args.target
    if not os.path.exists(target):
        print(f"Error: Target path '{target}' does not exist.")
        sys.exit(1)

    print(f"🛡️ [SAPQ Engine v1.0] Running 4-Tier Contradiction Matrix Audit on: {target}")

    if os.path.isfile(target):
        res = audit_file(target, baseline_filepath=args.baseline, audit_only=args.audit_only)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"📊 Audit Integrity Score: {res.get('audit_integrity_score', 0)}/100")
            print(f"Total Lines: {res.get('total_lines', 0)}")
            print(f"Discontinuities (Torsion Crossings): {len(res.get('discontinuities_detected', []))}")
            print(f"Zombie Nodes (Ghost Variables): {len(res.get('zombie_nodes_detected', []))}")
            print(f"Event Target Mismatches: {len(res.get('event_target_mismatches', []))}")
            if res.get('discontinuities_detected'):
                print("\n⚠️ Torsion Crossings:")
                for item in res['discontinuities_detected']:
                    print(f"  - {item['symbol']}: ref at L{item['ref_line']} before def at L{item['def_line']}")
            if res.get('event_target_mismatches'):
                print("\n⚠️ Event Target Mismatches (Phase 18):")
                for item in res['event_target_mismatches']:
                    print(f"  - {item['issue']}")
            if res.get('missing_intended_features'):
                print("\n⚠️ Missing Intended Features (Phase 20 Baseline Hole):")
                for item in res['missing_intended_features']:
                    print(f"  - {item['issue']}")

            if res.get('causality_contradictions'):
                print(f"Causality Contradictions: {len(res['causality_contradictions'])}")
            if res.get('mockup_hallucinations'):
                print(f"Mockup Hallucinations: {len(res['mockup_hallucinations'])}")
            if res.get('cascade_graph_issues'):
                print(f"Cascade Graph Issues: {len(res['cascade_graph_issues'])}")
            if res.get('python_subprocess_issues'):
                print(f"Python Subprocess Issues: {len(res['python_subprocess_issues'])}")
            if res.get('spec_mismatches'):
                print(f"Spec Mismatches: {len(res['spec_mismatches'])}")
            if res.get('dom_relay_orchestrated'):
                print("DOM Relay: Orchestrated via HTML Proxy Map")

            if args.interrogate and not args.audit_only:
                session_id = os.path.basename(target).split('.')[0]
                arbiter = SAPQArbiter(session_id=session_id)
                arbiter.log_patch_attempt(res.get('audit_integrity_score', 0), len(res.get('missing_intended_features', [])))
                dossier = arbiter.generate_interrogation_dossier(
                    target,
                    baseline_issues=res.get('missing_intended_features', []),
                    generic_issues=res.get('discontinuities_detected', []) + res.get('event_target_mismatches', [])
                )
                if dossier:
                    print("\n🤖 [SAPQ Phase 21] LLM INTERROGATION DOSSIER GENERATED:")
                    print(dossier)
    elif os.path.isdir(target):
        results = audit_directory(target, audit_only=args.audit_only)
        perfect = sum(1 for r in results if r['audit_integrity_score'] == 100)
        total_cnt = max(1, len(results))
        pct = (perfect / total_cnt) * 100
        print(f"\n📊 Total Files Audited: {len(results)}")
        print(f"✅ Perfect 100-Score Files: {perfect}/{len(results)} ({pct:.1f}%)")

if __name__ == "__main__":
    main()
