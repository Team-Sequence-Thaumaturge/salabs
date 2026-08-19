from __future__ import annotations

import json
from pathlib import Path

from upload.sapq_ast_parser import ASTParser
from upload.sapq_dom_relay import SAPQDOMRelay

ROOT = Path('/home/ubuntu/sapq_review_fixtures')
python_fixture = ROOT / 'unused_python_function.py'
html_fixture = ROOT / 'missing_dom_target.html'

ast_parser = ASTParser(str(python_fixture))
ast_result = {}
for method in ('get_all_identifier_usages', 'detect_torsion_crossings', 'detect_mockup_hallucinations'):
    try:
        value = getattr(ast_parser, method)()
        ast_result[method] = {'ok': True, 'value': sorted(value) if isinstance(value, set) else value}
    except Exception as exc:
        ast_result[method] = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}

relay_result = {}
try:
    relay = SAPQDOMRelay(str(html_fixture))
    nav_map = relay.generate_navigation_map()
    relay_result = {'ok': True, 'element_count': len(nav_map), 'first_element': nav_map[0] if nav_map else None}
except Exception as exc:
    relay_result = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}

print(json.dumps({'python_ast_adapter': ast_result, 'dom_relay': relay_result}, ensure_ascii=False, indent=2))
