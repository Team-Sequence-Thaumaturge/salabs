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

import numpy as np

class SpatialProjector:
    """
    SpatialProjector: Maps AIT Architecture Blueprints into 3D Spatial Tensors.
    Converts V1~V4 parsing node data into GPGPU serializable JSON/Float32Array dicts.
    """
    def __init__(self, target_filepath=None, gamma=0.5, epsilon=0.01, beta_torsion=0.1):
        self.target_filepath = target_filepath
        if target_filepath:
            self.engine = MultiVectorCrossParsingAuditEngine(target_filepath)

        self.gamma = gamma
        self.epsilon = epsilon
        self.beta_torsion = beta_torsion
        self.x_sink = np.array([10.0, 10.0, 5.0]) # Target critical Gravity Sink

    def get_potential(self, x, s, d):
        """
        Compute Potential Scalar Field Phi(x)
        """
        dist_sq = np.sum((x - self.x_sink)**2)
        phi = (self.gamma * s * d) / (dist_sq + self.epsilon)
        return phi

    def get_potential_gradient(self, x, s, d):
        """
        Calculate Partial Derivatives del(Phi) / del(x^sigma)
        """
        dist_sq = np.sum((x - self.x_sink)**2)
        denominator = (dist_sq + self.epsilon)**2
        grad = -2.0 * self.gamma * s * d * (x - self.x_sink) / (denominator + 1e-12)
        return grad

    def get_christoffel_symbols(self, x, s, d):
        """
        Evaluate symmetric Levi-Civita Connection symbols gamma^lambda_mu_nu
        """
        grad = self.get_potential_gradient(x, s, d) # 3-dim vector
        gamma_symbols = np.zeros((3, 3, 3)) # [lambda, mu, nu]
        eta = np.eye(3) # Flat Euclidean metric

        for lam in range(3):
            for mu in range(3):
                for nu in range(3):
                    # - ( delta^lam_mu * d_nu(Phi) + delta^lam_nu * d_mu(Phi) - eta_mu_nu * d^lam(Phi) )
                    term1 = (1.0 if lam == mu else 0.0) * grad[nu]
                    term2 = (1.0 if lam == nu else 0.0) * grad[mu]
                    term3 = eta[mu, nu] * grad[lam] # eta^lam_sigma * d_sigma(Phi)
                    gamma_symbols[lam, mu, nu] = -(term1 + term2 - term3)

        return gamma_symbols

    def get_contorsion_symbols(self, x, s, d, c):
        """
        Evaluate Contorsion symbols K^lambda_mu_nu mapped from Taint Severity Tensors
        """
        T = np.zeros((3, 3, 3)) # Torsion Tensor [lambda, mu, nu]
        # Map indices: 0->S, 1->D, 2->C
        T[0, 1, 2] = self.beta_torsion * c
        T[0, 2, 1] = -self.beta_torsion * c
        T[1, 2, 0] = self.beta_torsion * d
        T[1, 0, 2] = -self.beta_torsion * d
        T[2, 0, 1] = self.beta_torsion * s
        T[2, 1, 0] = -self.beta_torsion * s

        K = np.zeros((3, 3, 3)) # Contorsion Tensor [lambda, mu, nu]
        for lam in range(3):
            for mu in range(3):
                for nu in range(3):
                    # K^lam_mu_nu = 1/2 * ( T^lam_mu_nu - T_mu^lam_nu - T_nu^lam_mu )
                    # Under diagonal conformal metric raising/lowering
                    K[lam, mu, nu] = 0.5 * (T[lam, mu, nu] - T[mu, lam, nu] - T[nu, lam, mu])

        return K

    def compute_autoparallel_path(self, start_pos, velocity, s, d, c, step_size=0.01, steps=200):
        """
        RK4 integrator to solve the autoparallel trajectory equations:
        d2x/ds2 = - (gamma + K) * dx/ds * dx/ds
        """
        state = np.zeros(6) # [x, y, z, vx, vy, vz]
        state[0:3] = start_pos
        state[3:6] = velocity

        path_points = []
        path_points.append(np.copy(state[0:3]))

        def derivatives(curr_state):
            x_val = curr_state[0:3]
            v_val = curr_state[3:6]

            gamma = self.get_christoffel_symbols(x_val, s, d)
            K = self.get_contorsion_symbols(x_val, s, d, c)
            gamma_total = gamma + K # Combined non-symmetric connection

            ax_ay_az = np.zeros(3)
            for lam in range(3):
                acc_sum = 0.0
                for mu in range(3):
                    for nu in range(3):
                        acc_sum += gamma_total[lam, mu, nu] * v_val[mu] * v_val[nu]
                ax_ay_az[lam] = -acc_sum

            dstateds = np.zeros(6)
            dstateds[0:3] = v_val
            dstateds[3:6] = ax_ay_az
            return dstateds

        curr_s = 0.0
        for _ in range(steps):
            # RK4 Integration steps
            k1 = derivatives(state)
            k2 = derivatives(state + (step_size/2.0)*k1)
            k3 = derivatives(state + (step_size/2.0)*k2)
            k4 = derivatives(state + step_size*k3)

            state += (step_size/6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4)
            path_points.append(np.copy(state[0:3]))
            curr_s += step_size

        return path_points

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
            sigma1 = (trace + math.sqrt(discriminant)) / 2
            sigma2 = (trace - math.sqrt(discriminant)) / 2
        else:
            sigma1 = trace / 2
            sigma2 = trace / 2

        # SVD Saliency Accretion (Top 10% Truncation, >= 90% energy)
        total_energy = sigma1**2 + sigma2**2
        acc_energy = 0
        sigma_core = 0
        for s in [sigma1, sigma2]:
            acc_energy += s**2
            sigma_core += s
            if total_energy > 0 and (acc_energy / total_energy) >= 0.90:
                break

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
                # T_{\mu\nu}^{\lambda} = \Gamma_{\mu\nu}^{\lambda} - \Gamma_{\nu\mu}^{\lambda} - \gamma_{\mu\nu}^{\lambda}
                gamma_mu_nu = ref_line / max(1, self.engine.total_lines)
                gamma_nu_mu = def_line / max(1, self.engine.total_lines)
                connection_coef = (gamma_mu_nu - gamma_nu_mu) * 0.1
                torsion = 5.0 * abs(gamma_mu_nu - gamma_nu_mu - connection_coef)

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
