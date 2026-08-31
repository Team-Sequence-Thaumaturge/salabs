import pytest
from sapq_engine import audit_omni_stream

def test_workslop_silent_failure():
    data = "try:\n    do_something()\nexcept:\n    pass\n"
    report = audit_omni_stream(data, "text/plain")
    issues = report["issues"]
    assert any("SILENT_FAILURE" in issue["type"] for issue in issues)

def test_workslop_zombie_wrapper():
    data = "def wrapper(x):\n    return wrapper(x)\n"
    report = audit_omni_stream(data, "text/plain")
    issues = report["issues"]
    assert any("ZOMBIE_WRAPPER" in issue["type"] for issue in issues)
    assert report["workslop_metrics"]["leach_score"] > 0

def test_workslop_degenerate_state():
    import base64
    b64 = "InvalidBase64!"
    report = audit_omni_stream(b64, "application/base64")
    # Base64 fails parsing, invariants valid is False -> torsion deviation should be 1.0
    assert report["workslop_metrics"]["torsion_deviation"] == 1.0

def test_workslop_clean_code():
    data = "def normal_func():\n    print('Hello World')\n"
    report = audit_omni_stream(data, "text/plain")
    assert report["workslop_metrics"]["index"] < 0.5
    assert report["workslop_metrics"]["leach_score"] == 0.0
