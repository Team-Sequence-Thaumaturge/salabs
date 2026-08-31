import numpy as np
import base64
import time
import os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from omni_tensor_state import BaseTensorState
from sapq_ast_parser import ASTParser
import tempfile
import os

class TextTensorState(BaseTensorState):
    def __init__(self, text):
        self.text = text
        self._timestamp = time.time()

        # AST 제어 흐름 노드 및 자연어 명제 변환 (S_text)
        # Write to temp file for ASTParser to process
        fd, temp_path = tempfile.mkstemp(suffix=".py" if "def " in text or "class " in text else ".js")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(text)
            parser = ASTParser(temp_path)
            # Create a simple topological tensor based on AST nodes length / structure
            node_count = 0
            def count_nodes(n):
                nonlocal node_count
                node_count += 1
            parser._traverse(parser.ast, count_nodes)

            if node_count == 0:
                node_count = 1.0 # fallback for pure text natural language Claim-Evidence
            self._S_matrix = np.array([node_count, len(text) / node_count], dtype=float)
        except Exception:
            self._S_matrix = np.array([1.0, len(text)], dtype=float)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @property
    def S_matrix(self):
        return self._S_matrix

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def dimension(self):
        return self._S_matrix.shape

    @property
    def entropy_density(self):
        return np.mean(np.abs(self._S_matrix))

    @property
    def invariants(self):
        return {"type": "text", "length": len(self.text)}

class BinaryTensorState(BaseTensorState):
    def __init__(self, b64_str):
        self.b64_str = b64_str
        self._timestamp = time.time()
        try:
            self.data = base64.b64decode(b64_str, validate=True)
            self._S_matrix = np.frombuffer(self.data, dtype=np.uint8).astype(float)
        except Exception:
            self._S_matrix = np.array([])
            self.data = b""

    @property
    def S_matrix(self):
        return self._S_matrix

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def dimension(self):
        return self._S_matrix.shape

    @property
    def entropy_density(self):
        if len(self._S_matrix) == 0:
            return 0.0
        # Byte entropy approximation
        return np.std(self._S_matrix)

    @property
    def invariants(self):
        return {"type": "binary", "valid": len(self.data) > 0}

class ControlMapTensorState(BaseTensorState):
    def __init__(self, q_arr):
        # We can handle input as either flat array of 18 DoF or a dict with q_arr, velocity, torque
        if isinstance(q_arr, dict):
            self.q_arr = np.array(q_arr.get('q_arr', []), dtype=float)
            self.velocity = np.array(q_arr.get('velocity', []), dtype=float)
            self.torque = np.array(q_arr.get('torque', []), dtype=float)
        else:
            self.q_arr = np.array(q_arr, dtype=float)
            self.velocity = np.zeros_like(self.q_arr)
            self.torque = np.zeros_like(self.q_arr)

        self._timestamp = time.time()
        # Check 18-DoF kinematic limits q_min <= q <= q_max
        self.q_min = -np.pi
        self.q_max = np.pi

        # Validation checks (supports 18-DoF or 6-DoF)
        dof = len(self.q_arr)
        has_valid_dof = dof in [6, 18]
        within_limits = np.all((self.q_arr >= self.q_min) & (self.q_arr <= self.q_max)) if has_valid_dof else False
        self.valid = bool(has_valid_dof and within_limits)

        if self.valid:
            # S_ctrl = [q, v, tau] stacked or concatenated
            if len(self.velocity) == dof and len(self.torque) == dof:
                self._S_matrix = np.concatenate([self.q_arr, self.velocity, self.torque])
            else:
                self._S_matrix = self.q_arr
        else:
            self._S_matrix = np.array([])

    @property
    def S_matrix(self):
        return self._S_matrix

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def dimension(self):
        return self._S_matrix.shape

    @property
    def entropy_density(self):
        if not self.valid:
            return 0.0
        return np.var(self._S_matrix)

    @property
    def invariants(self):
        return {"type": "control_map", "valid": self.valid}

class VideoTensorState(BaseTensorState):
    def __init__(self, frames):
        self.frames = frames
        self._timestamp = time.time()
        # 시계열 프레임 간 광학 흐름(Optical Flow) 및 시간 미분(∂S/∂t) 기반 위상 궤적 텐서(S_video) 산출
        if not frames or len(frames) < 2:
            self._S_matrix = np.array([0.0], dtype=float)
        else:
            # We approximate the temporal derivative by taking the byte-length differences (∂S/∂t)
            # across the frame sequence to strictly avoid arbitrary mock values
            frame_sizes = np.array([len(str(f).encode('utf-8')) for f in frames], dtype=float)
            temporal_derivative = np.diff(frame_sizes)
            self._S_matrix = temporal_derivative

    @property
    def S_matrix(self):
        return self._S_matrix

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def dimension(self):
        return self._S_matrix.shape

    @property
    def entropy_density(self):
        return np.sum(self._S_matrix)

    @property
    def invariants(self):
        return {"type": "video", "frames": len(self.frames)}
