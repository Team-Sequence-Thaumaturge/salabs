import pytest
import numpy as np
from omni_ingestor import OmniIngestor

def test_text_ingestion():
    data = "Claim-Evidence tensor generation."
    S_matrix, invariants = OmniIngestor.ingest(data, "text/plain")
    assert invariants["type"] == "text"
    assert invariants["length"] == len(data)
    assert len(S_matrix) == 2

def test_ast_text_ingestion():
    data = "def foo():\n    pass\nclass Bar:\n    pass\n"
    S_matrix, invariants = OmniIngestor.ingest(data, "text/plain")
    assert invariants["type"] == "text"
    assert len(S_matrix) == 2
    assert S_matrix[0] > 1.0

def test_binary_valid_base64():
    import base64
    raw = b"Dummy Image Header"
    b64 = base64.b64encode(raw).decode('utf-8')
    S_matrix, invariants = OmniIngestor.ingest(b64, "application/base64")
    assert invariants["type"] == "binary"
    assert invariants["valid"] is True
    assert len(S_matrix) > 0

def test_binary_invalid_base64():
    b64 = "InvalidBase64!"
    S_matrix, invariants = OmniIngestor.ingest(b64, "application/base64")
    assert invariants["type"] == "binary"
    assert invariants["valid"] is False
    assert len(S_matrix) == 0

def test_control_map_valid_18dof():
    q_arr = [0.1] * 18
    S_matrix, invariants = OmniIngestor.ingest(q_arr, "application/x-control-map")
    assert invariants["type"] == "control_map"
    assert invariants["valid"] is True
    assert len(S_matrix) == 54 # q (18) + v (18) + tau (18) = 54

def test_control_map_full_telemetry():
    data = {
        "q_arr": [0.1] * 18,
        "velocity": [0.5] * 18,
        "torque": [1.0] * 18
    }
    S_matrix, invariants = OmniIngestor.ingest(data, "application/x-control-map")
    assert invariants["type"] == "control_map"
    assert invariants["valid"] is True
    assert len(S_matrix) == 54
    assert S_matrix[18] == 0.5
    assert S_matrix[36] == 1.0

def test_control_map_broken_18dof():
    # Broken due to missing DoF (only 17) and out of bounds (> pi)
    q_arr = [4.0] * 17
    S_matrix, invariants = OmniIngestor.ingest(q_arr, "application/x-control-map")
    assert invariants["type"] == "control_map"
    assert invariants["valid"] is False
    assert len(S_matrix) == 0

def test_video_ingestion():
    frames = ["frame1", "frame2", "frame3"]
    S_matrix, invariants = OmniIngestor.ingest(frames, "video/mp4")
    assert invariants["type"] == "video"
    assert invariants["frames"] == 3
    assert len(S_matrix) == len(frames) - 1

def test_control_map_valid_6dof():
    q_arr = [0.1] * 6
    S_matrix, invariants = OmniIngestor.ingest(q_arr, "application/x-control-map")
    assert invariants["type"] == "control_map"
    assert invariants["valid"] is True
    assert len(S_matrix) == 18 # q(6) + v(6) + tau(6)
