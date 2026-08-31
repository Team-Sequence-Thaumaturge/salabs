from __future__ import annotations
import sys, os
sys.path.insert(0, r'C:\stella\project\sandbox\salabs-jules-sandbox\modules\sapq')


import json
import shutil
from pathlib import Path

from sapq_engine import audit_file

ROOT = Path('C:/stella/project/sandbox/salabs-jules-sandbox/temp_sapq_newest_fixtures')
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)

FIXTURES = {
    'valid_function_hoist.js': """callLater();
function callLater() { return 42; }
""",
    'python_unused.py': """def unused_helper():
    return 42
""",
    'python_mockup.py': """def pay():
    return True
""",
    'invalid_syntax.py': """def broken(:
    return 1
""",
    'invalid_syntax.js': """function broken( {
  return 1;
}
""",
    'interlock_multiline.js': """const state = { active: true };
if (state.active) {
  document.querySelector('#b').disabled = true;
}
""",
    'async_race.js': """let ready = false;
Promise.resolve().then(() => { ready = true; });
if (!ready) { render(); }
function render() { return 'rendered'; }
""",
    'mockup_return_true.js': """function pay() { return true; }
""",
    'phase4_last_line.js': """const first = 1;
const second = 2;
const third = 3;
const fourth = 4;
setTimeout(() => {}, 0);
""",
    'missing_dom_target.html': """<!doctype html><html><body>
<button id="run" onclick="document.getElementById('missing_target').click()">Run</button>
</body></html>
""",
    'undeclared_symbol.js': """function runner() {
  return unboundValue + 1;
}
runner();
""",
}

for filename, content in FIXTURES.items():
    (ROOT / filename).write_text(content, encoding='utf-8')

summary: dict[str, object] = {}
for filename in FIXTURES:
    try:
        result = audit_file(
            str(ROOT / filename),
            session_id=f"newest_{Path(filename).stem}",
            audit_only=True,
        )
        summary[filename] = {
            'ok': True,
            'score': result.get('audit_integrity_score'),
            'preflight': result.get('preflight_status'),
            'syntax_errors': result.get('syntax_errors', []),
            'discontinuities': result.get('discontinuities_detected', []),
            'zombies': result.get('zombie_nodes_detected', []),
            'event_mismatches': result.get('event_target_mismatches', []),
            'undeclared': result.get('scope_undeclared_symbols', []),
            'mockups': result.get('mockup_hallucinations', []),
            'causalities': result.get('causality_contradictions', []),
            'intent_mismatches': result.get('spec_mismatches', []),
            'runtime_errors': result.get('runtime_console_errors', []),
            'interlock_status': result.get('interlock_status'),
            'vector_nodes': result.get('vector_nodes', {}),
        }
    except Exception as exc:
        summary[filename] = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}

state_artifacts = sorted(
    str(path.relative_to(ROOT))
    for path in ROOT.rglob('*')
    if path.name.startswith('.sapq_') or '.sapq_' in path.parts
)
summary['audit_only_state_artifacts'] = state_artifacts

print(json.dumps(summary, ensure_ascii=False, indent=2))
