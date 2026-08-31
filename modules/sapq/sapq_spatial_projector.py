import math
import hashlib
import sys
import os

try:
    from multi_vector_parser import MultiVectorCrossParsingAuditEngine
except ImportError:
    # Handle absolute or relative imports depending on how the module is executed
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from multi_vector_parser import MultiVectorCrossParsingAuditEngine

class SpatialProjector:
    """
    SpatialProjector: Maps AIT Architecture Blueprints into 3D Spatial Tensors.
    Converts V1~V4 parsing node data into GPGPU serializable JSON/Float32Array dicts.
    """
    def __init__(self, target_filepath):
        self.target_filepath = target_filepath
        self.engine = MultiVectorCrossParsingAuditEngine(target_filepath)

    def _deterministic_hash(self, text):
        """Generates a deterministic float between 0 and 1 from a string to avoid Math.random()."""
        h = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return int(h[:8], 16) / 0xffffffff

    def generate_tensors(self):
        """Generates the 3D spatial tensors from the parsed file data."""
        # Phase 1: Retrieve V1-V4 Vectors
        v1_forward = self.engine.parse_phase_1_forward()
        v2_backward = self.engine.parse_phase_2_backward()
        v3_skip = self.engine.parse_phase_3_skip_forward()
        v4_skip_back = self.engine.parse_phase_4_skip_backward()

        # Execute linking for discontinuities
        report = self.engine.execute_vector_end_trajectory_linking()
        discontinuities = report.get("discontinuities_detected", [])

        count = len(v1_forward)

        # Initialize Float32Array equivalents
        positions = []
        colors = []
        torsionTensors = []
        reconciliationVectors = []
        gravitySinks = []

        if count == 0:
            return {
                "count": 0,
                "positions": positions,
                "colors": colors,
                "torsionTensors": torsionTensors,
                "reconciliationVectors": reconciliationVectors,
                "gravitySinks": gravitySinks
            }

        # [SVD Saliency]: Construct proxy covariance matrix of dependencies
        mean_v1 = sum(t["line"] for t in v1_forward) / max(1, count)
        mean_v2 = sum(t["line"] for t in v2_backward) / max(1, len(v2_backward))

        cov_11 = sum(((t["line"] - mean_v1) ** 2) for t in v1_forward) / max(1, count)
        cov_22 = sum(((t["line"] - mean_v2) ** 2) for t in v2_backward) / max(1, len(v2_backward))

        cov_12 = 0
        min_len = min(len(v1_forward), len(v2_backward))
        if min_len > 0:
            cov_12 = sum(((v1_forward[i]["line"] - mean_v1) * (v2_backward[i]["line"] - mean_v2)) for i in range(min_len)) / min_len

        # Singular Value Decomposition proxy (eigenvalues of 2x2 covariance)
        trace = cov_11 + cov_22
        det = cov_11 * cov_22 - cov_12 ** 2
        discriminant = trace**2 - 4*det

        if discriminant > 0:
            sigma_core = (trace + math.sqrt(discriminant)) / 2
        else:
            sigma_core = trace / 2

        saliency_factor = sigma_core / (sigma_core + 1.0) if sigma_core > 0 else 0.5

        disc_map = {d["symbol"]: d for d in discontinuities}

        # [Wave Mechanics]: Asynchronous loop phase lag
        v4_count = len(v4_skip_back)
        phase_lag = (v4_count * math.pi) / max(1, count)

        for i, token in enumerate(v1_forward):
            symbol = token.get("symbol", f"unknown_{i}")
            line_num = token.get("line", 0)

            # [Scaffold Geometry]: Complex Potential W(z) = phi + i*psi
            h1 = self._deterministic_hash(symbol + "_r")
            h2 = self._deterministic_hash(symbol + "_theta")

            r_val = 10.0 * h1 * saliency_factor
            theta = 2.0 * math.pi * h2

            z_real = r_val * math.cos(theta)
            z_imag = r_val * math.sin(theta)

            phi = z_real**2 - z_imag**2
            psi = 2 * z_real * z_imag

            # Invariant Attractor (Anchor A)
            anchor_x = phi
            anchor_y = psi
            anchor_z = (line_num / max(1, self.engine.total_lines)) * 10.0

            # [Riemannian Torsion]: Calculate curvature T based on discontinuities
            torsion = 0.0
            if symbol in disc_map:
                def_line = disc_map[symbol].get("def_line", 0)
                ref_line = disc_map[symbol].get("ref_line", 0)
                torsion = 5.0 * abs(ref_line - def_line) / max(1, self.engine.total_lines)

            # Apply Wave Mechanics interference to disturbed position
            interference = math.cos(anchor_x - anchor_y + phase_lag)

            # Disturbed position A^c
            pos_x = anchor_x + torsion * interference
            pos_y = anchor_y + torsion * math.sin(phase_lag)
            pos_z = anchor_z + torsion * math.cos(phase_lag)

            positions.extend([pos_x, pos_y, pos_z])

            # Semantic Colors (RGB)
            if torsion > 0.1:
                colors.extend([1.0, 0.2, 0.2]) # High torsion (Red)
            elif "FORWARD_DEF" in token.get("type", ""):
                colors.extend([0.2, 0.4, 1.0]) # Standard def (Blue)
            else:
                colors.extend([0.2, 1.0, 0.5]) # Safe (Green)

            torsionTensors.extend([torsion, torsion * 0.5, torsion * 0.2])

            # [Reconciliation Vector]: Geodesic flow back to Invariant Anchor (A - A^c)
            rec_x = anchor_x - pos_x
            rec_y = anchor_y - pos_y
            rec_z = anchor_z - pos_z
            reconciliationVectors.extend([rec_x, rec_y, rec_z])

            # Gravity Sinks
            sink_depth = torsion * saliency_factor
            gravitySinks.extend([pos_x, pos_y, pos_z, sink_depth])

        return {
            "count": count,
            "positions": positions,
            "colors": colors,
            "torsionTensors": torsionTensors,
            "reconciliationVectors": reconciliationVectors,
            "gravitySinks": gravitySinks
        }
