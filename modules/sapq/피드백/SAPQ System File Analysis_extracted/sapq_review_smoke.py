from __future__ import annotations

import json
import shutil
from pathlib import Path

from upload.sapq_engine import audit_file

ROOT = Path('/home/ubuntu/sapq_review_fixtures')
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
    'valid_simple.js': """function greet(name) { return name; }
greet('SAPQ');
""",
    'missing_dom_target.html': """<!doctype html><html><body>
<button id="run" onclick="document.getElementById('missing_target').click()">Run</button>
</body></html>
""",
    'interlock_desync.js': """const state = { active: true };
if (state.active) {
  document.querySelector('#b').disabled = true;
}
""",
    'async_race.js': """let ready = false;
Promise.resolve().then(() => { ready = true; });
if (!ready) { render(); }
function render() { return 'rendered'; }
""",
    'baseline_state_dom.js': """function renderFromState(state) {
  document.body.innerHTML = state.message;
}
""",
    'target_without_state_dom.js': """function noop() {
  return 1;
}
""",
}

for filename, content in FIXTURES.items():
    (ROOT / filename).write_text(content, encoding='utf-8')

summary = {}
for filename in FIXTURES:
    result = audit_file(str(ROOT / filename), session_id=f"review_{Path(filename).stem}")
    summary[filename] = {
        'score': result.get('audit_integrity_score'),
        'preflight': result.get('preflight_status'),
        'discontinuities': result.get('discontinuities_detected', []),
        'zombies': result.get('zombie_nodes_detected', []),
        'event_mismatches': result.get('event_target_mismatches', []),
        'vector_nodes': result.get('vector_nodes', {}),
    }

baseline_result = audit_file(
    str(ROOT / 'target_without_state_dom.js'),
    session_id='review_baseline_gap',
    baseline_filepath=str(ROOT / 'baseline_state_dom.js'),
)
summary['baseline_comparison'] = {
    'score': baseline_result.get('audit_integrity_score'),
    'missing_intended_features': baseline_result.get('missing_intended_features', []),
}

print(json.dumps(summary, indent=2, ensure_ascii=False))
