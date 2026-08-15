import sys
import os
import json
import argparse
from .sapq_engine import SAPQEngine, audit_file, audit_directory

def main():
    parser = argparse.ArgumentParser(description="SAPQ - Sequence Autonomic Parsing & QA CLI Engine")
    parser.add_argument("target", help="Target file or directory path to audit")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")
    args = parser.parse_args()

    target = args.target
    if not os.path.exists(target):
        print(f"Error: Target path '{target}' does not exist.")
        sys.exit(1)

    print(f"🛡️ [SAPQ Engine v1.0] Running 4-Tier Contradiction Matrix Audit on: {target}")

    if os.path.isfile(target):
        res = audit_file(target)
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
    elif os.path.isdir(target):
        results = audit_directory(target)
        perfect = sum(1 for r in results if r['audit_integrity_score'] == 100)
        total_cnt = max(1, len(results))
        pct = (perfect / total_cnt) * 100
        print(f"\n📊 Total Files Audited: {len(results)}")
        print(f"✅ Perfect 100-Score Files: {perfect}/{len(results)} ({pct:.1f}%)")

if __name__ == "__main__":
    main()
