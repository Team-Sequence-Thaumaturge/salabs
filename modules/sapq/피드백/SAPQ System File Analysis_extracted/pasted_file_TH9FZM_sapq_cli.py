import sys
import os
import json
import argparse
try:
    from .sapq_engine import SAPQEngine, audit_file, audit_directory
    from .sapq_arbiter import SAPQArbiter
except (ImportError, ValueError):
    from sapq_engine import SAPQEngine, audit_file, audit_directory
    from sapq_arbiter import SAPQArbiter

def main():
    parser = argparse.ArgumentParser(description="SAPQ - Sequence Autonomic Parsing & QA CLI Engine")
    parser.add_argument("target", help="Target file or directory path to audit")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")
    parser.add_argument("--baseline", type=str, help="Baseline original file for Phase 20 Hyper-Isomorphic auditing")
    parser.add_argument("--interrogate", action="store_true", help="Phase 21: Generate LLM Interrogation Dossier if holes exist")
    parser.add_argument("--audit-only", action="store_true", help="Run in non-destructive read-only audit mode")
    args = parser.parse_args()

    target = args.target
    if not os.path.exists(target):
        print(f"Error: Target path '{target}' does not exist.")
        sys.exit(1)

    print(f"🛡️ [SAPQ Engine v1.0] Running 4-Tier Contradiction Matrix Audit on: {target}")

    import re
    session_id = re.sub(r'[^A-Za-z0-9_-]', '_', os.path.basename(target).split('.')[0])

    if os.path.isfile(target):
        res = audit_file(target, session_id=session_id, baseline_filepath=args.baseline, audit_only=args.audit_only)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"📊 Audit Integrity Score: {res.get('audit_integrity_score', 0)}/100")
            print(f"Total Lines: {res.get('total_lines', 0)}")
            print(f"Discontinuities (Torsion Crossings): {len(res.get('discontinuities_detected', []))}")
            print(f"Zombie Nodes (Ghost Variables): {len(res.get('zombie_nodes_detected', []))}")
            print(f"Event Target Mismatches: {len(res.get('event_target_mismatches', []))}")
            print(f"Scope Undeclared Symbols (ReferenceError Trap): {len(res.get('scope_undeclared_symbols', []))}")
            if res.get('discontinuities_detected'):
                print("\n⚠️ Torsion Crossings:")
                for item in res['discontinuities_detected']:
                    print(f"  - {item['symbol']}: ref at L{item['ref_line']} before def at L{item['def_line']}")
            if res.get('event_target_mismatches'):
                print("\n⚠️ Event Target Mismatches (Phase 18):")
                for item in res['event_target_mismatches']:
                    print(f"  - {item['issue']}")
            if res.get('scope_undeclared_symbols'):
                print("\n⚠️ Scope Undeclared Symbols (ReferenceError Trap):")
                for item in res['scope_undeclared_symbols']:
                    print(f"  - {item['issue']} at L{item['line']}")
            if res.get('missing_intended_features'):
                print("\n⚠️ Missing Intended Features (Phase 20 Baseline Hole):")
                for item in res['missing_intended_features']:
                    print(f"  - {item['issue']}")

            if args.interrogate and not args.audit_only:
                arbiter = SAPQArbiter(session_id=session_id)
                arbiter.log_patch_attempt(res.get('audit_integrity_score', 0), len(res.get('missing_intended_features', [])))
                dossier = arbiter.generate_interrogation_dossier(
                    target,
                    baseline_issues=res.get('missing_intended_features', []),
                    generic_issues=res.get('discontinuities_detected', []) + res.get('event_target_mismatches', []) + res.get('scope_undeclared_symbols', [])
                )
                if dossier:
                    print("\n🤖 [SAPQ Phase 21] LLM INTERROGATION DOSSIER GENERATED:")
                    print(dossier)
    elif os.path.isdir(target):
        # We also need to pass audit_only if we were to support it in audit_directory, but for now just pass to it if we modify it
        results = audit_directory(target, audit_only=args.audit_only)
        perfect = sum(1 for r in results if r['audit_integrity_score'] == 100)
        total_cnt = max(1, len(results))
        pct = (perfect / total_cnt) * 100
        print(f"\n📊 Total Files Audited: {len(results)}")
        print(f"✅ Perfect 100-Score Files: {perfect}/{len(results)} ({pct:.1f}%)")

if __name__ == "__main__":
    main()
