from __future__ import annotations

import json
import shutil
from pathlib import Path

from sapq_mv_latest.multi_vector_parser import MultiVectorCrossParsingAuditEngine
from sapq_mv_latest.sapq_engine import audit_file

ROOT = Path('/home/ubuntu/sapq_mv_fixtures')
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)

FIXTURES = {
    'valid_function_hoist.js': """callLater();
function callLater() { return 42; }
""",
    'phase4_last_line.js': """const first = 1;
const second = 2;
const third = 3;
const fourth = 4;
setTimeout(() => {}, 0);
""",
    'mixed_async.js': """async function load() {
  await fetch('/api').then(handle);
}
""",
    'dummy_timeout.js': """setTimeout(() => { resolve('ok'); }, 10);
""",
    'state_desync.js': """const state = { active: true };
if (state.active) {
  document.querySelector('#b').disabled = true;
}
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
    filepath = str(ROOT / filename)
    row: dict[str, object] = {}
    try:
        vector = MultiVectorCrossParsingAuditEngine(filepath).execute_vector_end_trajectory_linking()
        row['multi_vector'] = vector
    except Exception as exc:
        row['multi_vector_error'] = f'{type(exc).__name__}: {exc}'

    try:
        primary = audit_file(filepath, session_id=f'mv_{Path(filename).stem}', audit_only=True)
        row['primary_engine'] = {
            'score': primary.get('audit_integrity_score'),
            'vector_nodes': primary.get('vector_nodes', {}),
            'discontinuities': primary.get('discontinuities_detected', []),
            'scope_undeclared': primary.get('scope_undeclared_symbols', []),
            'causalities': primary.get('causality_contradictions', []),
            'interlock_status': primary.get('interlock_status'),
        }
    except Exception as exc:
        row['primary_engine_error'] = f'{type(exc).__name__}: {exc}'
    summary[filename] = row

summary['primary_alias_module'] = audit_file.__module__
print(json.dumps(summary, ensure_ascii=False, indent=2))
