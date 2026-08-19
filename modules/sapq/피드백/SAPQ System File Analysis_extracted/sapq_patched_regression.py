from __future__ import annotations

import json
import shutil
from pathlib import Path

from sapq_patched.sapq_ast_parser import ASTParser
from sapq_patched.sapq_engine import audit_file
from sapq_patched.sapq_interlock import SAPQInterlock

ROOT = Path('/home/ubuntu/sapq_patched_fixtures')
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)

FIXTURES = {
    'valid_function_hoist.js': """callLater();
function callLater() { return 42; }
""",
    'unused_python_function.py': """def unused_helper():
    return 42
""",
    'interlock_multiline.js': """const state = { active: true };
if (state.active) {
  document.querySelector('#b').disabled = true;
}
""",
    'interlock_same_line.js': """state.active = true; button.disabled = true;
""",
    'async_race.js': """let ready = false;
Promise.resolve().then(() => { ready = true; });
if (!ready) { render(); }
function render() { return 'rendered'; }
""",
    'mockup_stub.js': """function pay() { return true; }
""",
    'python_subprocess.py': """import subprocess
subprocess.run(['echo', 'not executed'])
""",
    'missing_dom_target.html': """<!doctype html><html><body>
<button id="run" onclick="document.getElementById('missing_target').click()">Run</button>
</body></html>
""",
    'unreferenced_js.js': """function unusedJsHelper() { return 1; }
""",
    'phase4_last_line.js': """const first = 1;
const second = 2;
const third = 3;
const fourth = 4;
setTimeout(() => {}, 0);
""",
}

for filename, content in FIXTURES.items():
    (ROOT / filename).write_text(content, encoding='utf-8')

summary: dict[str, object] = {}
for filename in FIXTURES:
    result = audit_file(str(ROOT / filename), session_id=f"patched_{Path(filename).stem}")
    summary[filename] = {
        'score': result.get('audit_integrity_score'),
        'preflight': result.get('preflight_status'),
        'discontinuities': result.get('discontinuities_detected', []),
        'zombies': result.get('zombie_nodes_detected', []),
        'causality': result.get('causality_contradictions', []),
        'mockups': result.get('mockup_hallucinations', []),
        'cascade': result.get('cascade_graph_issues', []),
        'python_subprocess': result.get('python_subprocess_issues', []),
        'event_mismatches': result.get('event_target_mismatches', []),
        'dom_relay_orchestrated': result.get('dom_relay_orchestrated', False),
        'has_spec_mismatches': 'spec_mismatches' in result,
        'vector_nodes': result.get('vector_nodes', {}),
    }

ast_parser = ASTParser(str(ROOT / 'unused_python_function.py'))
ast_methods = {}
for method in ('get_all_identifier_usages', 'detect_torsion_crossings', 'detect_mockup_hallucinations'):
    try:
        value = getattr(ast_parser, method)()
        ast_methods[method] = {'ok': True, 'value': sorted(value) if isinstance(value, set) else value}
    except Exception as exc:
        ast_methods[method] = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
summary['python_ast_public_methods'] = ast_methods

try:
    audit_only_result = audit_file(
        str(ROOT / 'unreferenced_js.js'),
        session_id='patched_audit_only',
        audit_only=True,
    )
    summary['audit_only'] = {
        'ok': True,
        'score': audit_only_result.get('audit_integrity_score'),
        'status': audit_only_result.get('session_context', '').splitlines()[1] if audit_only_result.get('session_context') else None,
    }
except Exception as exc:
    summary['audit_only'] = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}

interlock = SAPQInterlock()
interlock_results = {}
for label, report in {
    'event_target_mismatch_only': {'event_target_mismatches': [{'issue': 'missing target'}]},
    'python_subprocess_issue_only': {'python_subprocess_issues': [{'issue': 'subprocess policy'}]},
    'cascade_issue_only': {'cascade_graph_issues': [{'issue': 'lifecycle lock'}]},
}.items():
    try:
        interlock_results[label] = {'ok': True, 'decision': interlock.evaluate_audit_report(report, strict_mode=True)}
    except Exception as exc:
        interlock_results[label] = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
summary['interlock_consumes_new_report_keys'] = interlock_results

print(json.dumps(summary, ensure_ascii=False, indent=2))
