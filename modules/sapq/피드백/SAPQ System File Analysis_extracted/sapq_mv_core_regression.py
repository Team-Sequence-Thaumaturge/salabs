from __future__ import annotations
import sys, os
sys.path.insert(0, r'C:\stella\project\sandbox\salabs-jules-sandbox\modules\sapq')


import importlib.util
import json
import shutil
from pathlib import Path

MODULE_PATH = 'C:/stella/project/sandbox/salabs-jules-sandbox/modules/sapq/sapq_ast_parser.py'
spec = importlib.util.spec_from_file_location('sapq_mv_core_under_test', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
Engine = module.MultiVectorCrossParsingAuditEngine

ROOT = Path('C:/stella/project/sandbox/salabs-jules-sandbox/temp_sapq_mv_core_fixtures')
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
}
for filename, content in FIXTURES.items():
    (ROOT / filename).write_text(content, encoding='utf-8')

summary = {}
for filename in FIXTURES:
    report = Engine(str(ROOT / filename)).execute_vector_end_trajectory_linking()
    summary[filename] = {
        'score': report['audit_integrity_score'],
        'vector_nodes': report['vector_nodes'],
        'discontinuities': report['discontinuities_detected'],
        'semantic': report['semantic_contradictions'],
        'async': report['async_timing_contradictions'],
        'intent': report['intent_mismatches'],
    }

print(json.dumps(summary, ensure_ascii=False, indent=2))
