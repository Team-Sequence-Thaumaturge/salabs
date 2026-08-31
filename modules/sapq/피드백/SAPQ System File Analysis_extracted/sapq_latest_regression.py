from __future__ import annotations
import sys, os
sys.path.insert(0, r'C:\stella\project\sandbox\salabs-jules-sandbox\modules\sapq')


import contextlib
import io
import json
import shutil
from pathlib import Path

from sapq_ast_parser import ASTParser
from sapq_engine import audit_file
from sapq_interlock import InterlockCircuitBreaker
from sapq_spec_matcher import SpecSemanticMatcher

ROOT = Path('C:/stella/project/sandbox/salabs-jules-sandbox/temp_sapq_latest_fixtures')
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)

FIXTURES = {
    'valid_function_hoist.js': """callLater();
function callLater() { return 42; }
""",
    'python_def.py': """def unused_helper():
    return 42
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
    'invalid_syntax.py': """def broken(:
    return 1
""",
    'invalid_syntax.js': """function broken( {
  return 1;
}
""",
}

for filename, content in FIXTURES.items():
    (ROOT / filename).write_text(content, encoding='utf-8')

summary: dict[str, object] = {}
raw_reports = {}
for filename in FIXTURES:
    try:
        result = audit_file(str(ROOT / filename))
        raw_reports[filename] = result
        summary[filename] = {
            'ok': True,
            'score': result.get('audit_integrity_score'),
            'discontinuities': result.get('discontinuities_detected', []),
            'zombies': result.get('zombie_nodes_detected', []),
            'mockups': result.get('mockups_detected', []),
            'python_warnings': result.get('python_popup_warnings', []),
            'spec_warnings': result.get('spec_alignment_warnings', []),
            'vector_nodes': result.get('vector_nodes', {}),
        }
    except Exception as exc:
        summary[filename] = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}

python_ast = ASTParser(str(ROOT / 'python_def.py'))
try:
    summary['python_ast_parser'] = {
        'ok': True,
        'torsion': python_ast.detect_torsion_crossings(),
        'mockups': python_ast.detect_mockup_hallucinations(),
    }
except Exception as exc:
    summary['python_ast_parser'] = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}

matcher = SpecSemanticMatcher('target frequency = 40', 'example.js', 'const targetFrequency = 20;')
summary['standalone_spec_matcher'] = matcher.audit_code_alignment()

interlock_decisions = {}
for filename in ('valid_function_hoist.js', 'mockup_return_true.js'):
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            InterlockCircuitBreaker.evaluate_audit_results([raw_reports[filename]])
        interlock_decisions[filename] = {'blocked': False, 'output': stdout.getvalue().strip()}
    except SystemExit as exc:
        interlock_decisions[filename] = {'blocked': exc.code == 1, 'exit_code': exc.code, 'output': stdout.getvalue().strip()}
summary['interlock_decisions'] = interlock_decisions

print(json.dumps(summary, ensure_ascii=False, indent=2))
