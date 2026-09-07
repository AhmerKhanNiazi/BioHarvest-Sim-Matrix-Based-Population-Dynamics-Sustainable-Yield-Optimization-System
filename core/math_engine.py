"""
BioHarvest-Sim: Mathematical Core Engine
========================================
Author: Applied Mathematician & Software Architect
Standard: ISO/IEC/IEEE 12207 & 27001, PEP-8 Compliant

Implements:
- Dynamic N x N Leslie Matrix formulation
- Eigendecomposition & Perron-Frobenius Spectral Analysis
- Spectral Decomposition & Diagonalization (L = P * D * P^-1)
- Stable Age Distribution & Fisher's Reproductive Values
- Demographic Metrics: Net Reproductive Rate (R0), Generation Time, Damping Ratio
- Sensitivity & Elasticity Matrices (Caswell perturbation theory)
- Harvesting Regimes: Uniform, Proportional/Stage-Specific, Constant Quota
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from scipy import linalg


class LeslieMatrixEngine:
    """
    Mathematical engine implementing age-structured matrix population models
    using Leslie Matrices, Spectral Decomposition, and Harvesting Dynamics.
    """

    def __init__(
        self,
        fecundity: Union[List[float], np.ndarray],
        survival: Union[List[float], np.ndarray],
        species_name: str = "Generic Species",
    ) -> None:
        """
        Initialize Leslie Matrix from age-class fecundity and survival rates.

        Parameters
        ----------
        fecundity : Union[List[float], np.ndarray]
            Fecundity rates [f_1, f_2, ..., f_n] for each age class (length N).
        survival : Union[List[float], np.ndarray]
            Survival probabilities [s_1, s_2, ..., s_{n-1}] between age classes (length N-1).
        species_name : str, optional
            Human-readable label for the population model.
        """
        self.species_name = species_name
        self.fecundity = np.array(fecundity, dtype=np.float64)
        self.survival = np.array(survival, dtype=np.float64)
        self.n_classes = len(self.fecundity)

        self._validate_parameters()
        self.matrix: np.ndarray = self._construct_matrix()

        # Cached spectral attributes
        self._eigenvalues: Optional[np.ndarray] = None
        self._eigenvectors: Optional[np.ndarray] = None
        self._left_eigenvectors: Optional[np.ndarray] = None
        self._dominant_idx: Optional[int] = None
        self._is_diagonalizable: Optional[bool] = None
        self._p_mat: Optional[np.ndarray] = None
        self._p_inv: Optional[np.ndarray] = None
        self._diag_d: Optional[np.ndarray] = None

        # Compute spectral decomposition upon initialization
        self._compute_spectral_decomposition()

    def _validate_parameters(self) -> None:
        """Validate dimensional and biological constraints on vital rates."""
        if self.n_classes < 2:
            raise ValueError(f"Leslie matrix requires at least 2 age classes, received {self.n_classes}.")
        if len(self.survival) != self.n_classes - 1:
            raise ValueError(
                f"Survival vector length ({len(self.survival)}) must be exactly N - 1 ({self.n_classes - 1})."
            )
        if np.any(self.fecundity < 0.0):
            raise ValueError("Fecundity rates must be strictly non-negative (f_i >= 0).")
        if np.any(self.survival < 0.0) or np.any(self.survival > 1.0):
            raise ValueError("Survival rates must be valid probabilities within [0.0, 1.0].")
        if np.sum(self.fecundity) == 0.0:
            raise ValueError("Population cannot reproduce: all fecundity terms are zero.")

    def _construct_matrix(self) -> np.ndarray:
        """
        Construct the N x N Leslie Matrix:
        L = [ [f_1, f_2, ..., f_{n-1}, f_n],
              [s_1,  0,  ...,    0,     0  ],
              [ 0,  s_2, ...,    0,     0  ],
              ...
              [ 0,   0,  ..., s_{n-1},  0  ] ]
        """
        matrix = np.zeros((self.n_classes, self.n_classes), dtype=np.float64)
        matrix[0, :] = self.fecundity
        for i in range(self.n_classes - 1):
            matrix[i + 1, i] = self.survival[i]
        return matrix

    def _compute_spectral_decomposition(self) -> None:
        """
        Compute eigenvalues, right eigenvectors, left eigenvectors,
        and assess diagonalizability (L = P * D * P^-1).
        """
        # Right eigendecomposition: L * v = lambda * v
        w, vr = linalg.eig(self.matrix)
        self._eigenvalues = w
        self._eigenvectors = vr

        # Left eigendecomposition: u^T * L = lambda * u^T  <=>  L^T * u = lambda * u
        w_left, vl = linalg.eig(self.matrix.T)
        self._left_eigenvectors = vl

        # Identify dominant eigenvalue (Perron-Frobenius root: lambda_1 = rho(L) >= 0)
        magnitudes = np.abs(w)
        max_mag = np.max(magnitudes)
        # Find candidate eigenvalues whose magnitude is maximal and whose imaginary part is negligible
        candidates = [
            i for i, val in enumerate(w)
            if np.isclose(np.abs(val), max_mag, atol=1e-5)
            and np.isclose(val.imag, 0.0, atol=1e-5)
            and val.real > 0.0
        ]
        if candidates:
            self._dominant_idx = max(candidates, key=lambda idx: w[idx].real)
        else:
            self._dominant_idx = int(np.argmax(np.real(w)))

        # Find corresponding left eigenvector matching dominant eigenvalue
        dom_val = w[self._dominant_idx]
        self._left_dominant_idx = int(np.argmin(np.abs(w_left - dom_val)))

        # Check condition number of modal matrix P for diagonalizability
        cond_num = np.linalg.cond(vr)
        if np.isfinite(cond_num) and cond_num < 1e12:
            self._is_diagonalizable = True
            self._p_mat = vr
            self._diag_d = np.diag(w)
            self._p_inv = linalg.inv(vr)
        else:
            self._is_diagonalizable = False
            self._p_mat = None
            self._diag_d = None
            self._p_inv = None

    @property
    def dominant_eigenvalue(self) -> float:
        """
        Intrinsic growth factor (lambda_1 = rho(L)).
        lambda_1 > 1: Growing population
        lambda_1 = 1: Stationary population
        lambda_1 < 1: Declining population
        """
        assert self._eigenvalues is not None and self._dominant_idx is not None
        dom_val = self._eigenvalues[self._dominant_idx]
        return float(np.real(dom_val))

    @property
    def intrinsic_growth_rate(self) -> float:
        """Intrinsic rate of natural increase: r = ln(lambda_1)."""
        dom = self.dominant_eigenvalue
        return float(np.log(dom)) if dom > 0 else -np.inf

    @property
    def stable_age_distribution(self) -> np.ndarray:
        """
        Normalized dominant right eigenvector (w = v_1 / sum(v_1)),
        representing the asymptotic proportion of population in each age class.
        """
        assert self._eigenvectors is not None and self._dominant_idx is not None
        v1 = np.real(self._eigenvectors[:, self._dominant_idx])
        # Orient positive
        if np.sum(v1) < 0:
            v1 = -v1
        v1 = np.maximum(v1, 0.0)
        sum_v1 = np.sum(v1)
        if sum_v1 == 0:
            return np.ones(self.n_classes) / self.n_classes
        return v1 / sum_v1

    @property
    def reproductive_values(self) -> np.ndarray:
        """
        Fisher's reproductive value distribution (normalized dominant left eigenvector u_1).
        Represents the relative expected future reproductive contribution of each age class.
        """
        assert self._left_eigenvectors is not None and self._left_dominant_idx is not None
        # Match left eigenvector to dominant eigenvalue
        u1 = np.real(self._left_eigenvectors[:, self._left_dominant_idx])
        if np.sum(u1) < 0:
            u1 = -u1
        u1 = np.maximum(u1, 0.0)
        # Normalize relative to age-class 1 (u1[0] = 1.0) if non-zero
        if u1[0] > 1e-12:
            return u1 / u1[0]
        sum_u1 = np.sum(u1)
        return u1 / sum_u1 if sum_u1 > 0 else np.ones(self.n_classes)

    @property
    def damping_ratio(self) -> float:
        """
        Damping ratio: rho = lambda_1 / |lambda_2|.
        Measures the exponential rate of convergence toward the stable age distribution.
        """
        assert self._eigenvalues is not None
        sorted_mags = np.sort(np.abs(self._eigenvalues))[::-1]
        if len(sorted_mags) >= 2 and sorted_mags[1] > 1e-12:
            return float(sorted_mags[0] / sorted_mags[1])
        return np.inf

    @property
    def net_reproductive_rate(self) -> float:
        """
        Net Reproductive Rate R0: The mean number of offspring a female produces
        over her entire lifetime.
        R0 = sum_{i=1}^n l_i * f_i, where l_1 = 1, l_i = prod_{j=1}^{i-1} s_j.
        """
        l_x = np.ones(self.n_classes, dtype=np.float64)
        for i in range(1, self.n_classes):
            l_x[i] = l_x[i - 1] * self.survival[i - 1]
        return float(np.sum(l_x * self.fecundity))

    @property
    def generation_time(self) -> float:
        """
        Mean generation time T_c: T_c = ln(R0) / r = ln(R0) / ln(lambda_1).
        Approximate mean age of mothers at childbirth.
        """
        r0 = self.net_reproductive_rate
        r = self.intrinsic_growth_rate
        if abs(r) > 1e-9 and r0 > 0:
            return float(np.log(r0) / r)
        # Cohort approximation if r ~ 0
        l_x = np.ones(self.n_classes, dtype=np.float64)
        for i in range(1, self.n_classes):
            l_x[i] = l_x[i - 1] * self.survival[i - 1]
        weighted_age = np.sum(np.arange(1, self.n_classes + 1) * l_x * self.fecundity)
        return float(weighted_age / r0) if r0 > 0 else float(self.n_classes)

    def is_primitive(self) -> bool:
        """
        Test whether the Leslie matrix is primitive (strictly ergodic).
        A non-negative matrix L is primitive if there exists k > 0 such that L^k > 0.
        By Perron-Frobenius, primitivity guarantees a strictly positive dominant eigenvalue
        strictly exceeding all others in absolute value.
        """
        # A Leslie matrix is primitive if and only if the greatest common divisor
        # of the cycle lengths (indices where f_i > 0) is 1.
        fertile_indices = [i + 1 for i, f in enumerate(self.fecundity) if f > 1e-12]
        if not fertile_indices:
            return False
        gcd_val = fertile_indices[0]
        for idx in fertile_indices[1:]:
            gcd_val = np.gcd(gcd_val, idx)
        return bool(gcd_val == 1)

    def compute_sensitivity_matrix(self) -> np.ndarray:
        """
        Compute Caswell's Sensitivity Matrix:
        S_{ij} = d(lambda_1) / d(L_{ij}) = (u_i * v_j) / (u^T * v)

        Returns
        -------
        np.ndarray
            N x N matrix of absolute sensitivities.
        """
        assert self._eigenvectors is not None and self._left_eigenvectors is not None
        v = np.real(self._eigenvectors[:, self._dominant_idx])
        u = np.real(self._left_eigenvectors[:, self._left_dominant_idx])

        # Ensure consistent sign
        if np.sum(v) < 0:
            v = -v
        if np.sum(u) < 0:
            u = -u

        denom = np.dot(u, v)
        if abs(denom) < 1e-12:
            denom = 1e-12
        sensitivity = np.outer(u, v) / denom
        return np.maximum(sensitivity, 0.0)

    def compute_elasticity_matrix(self) -> np.ndarray:
        """
        Compute Caswell's Elasticity Matrix:
        E_{ij} = (L_{ij} / lambda_1) * (d(lambda_1) / d(L_{ij}))

        Elasticities represent proportional contributions of vital rates to lambda_1
        and always sum to exactly 1.0 (Euler's homogeneous function theorem).

        Returns
        -------
        np.ndarray
            N x N matrix of proportional elasticities.
        """
        sensitivity = self.compute_sensitivity_matrix()
        lam = self.dominant_eigenvalue
        if lam < 1e-12:
            lam = 1e-12
        elasticity = (self.matrix / lam) * sensitivity
        total_e = np.sum(elasticity)
        if total_e > 1e-9:
            elasticity /= total_e
        return elasticity

    def fast_predict_trajectory(
        self,
        x0: Union[List[float], np.ndarray],
        steps: int,
    ) -> np.ndarray:
        """
        Predict population trajectory over k time steps using Spectral Diagonalization:
        x_k = L^k * x0 = P * D^k * P^-1 * x0.
        Falls back to iterative matrix powers if matrix is defective.

        Parameters
        ----------
        x0 : Union[List[float], np.ndarray]
            Initial population vector across age classes (length N).
        steps : int
            Number of time steps to project.

        Returns
        -------
        np.ndarray
            (steps + 1) x N matrix where row t is the population vector at time t.
        """
        x_curr = np.array(x0, dtype=np.float64).reshape(-1, 1)
        if len(x_curr) != self.n_classes:
            raise ValueError(f"Initial population vector length ({len(x_curr)}) != {self.n_classes}.")

        trajectory = np.zeros((steps + 1, self.n_classes), dtype=np.float64)
        trajectory[0, :] = x_curr.flatten()

        if self._is_diagonalizable and self._p_mat is not None and self._p_inv is not None:
            # c = P^-1 * x0
            c = self._p_inv @ x_curr
            lambdas = self._eigenvalues
            for k in range(1, steps + 1):
                # D^k * c
                d_k_c = (lambdas ** k).reshape(-1, 1) * c
                # x_k = P * (D^k * c)
                xk = np.real(self._p_mat @ d_k_c).flatten()
                trajectory[k, :] = np.maximum(xk, 0.0)
        else:
            # Fallback for defective or ill-conditioned matrices
            for k in range(1, steps + 1):
                x_curr = self.matrix @ x_curr
                trajectory[k, :] = np.maximum(x_curr.flatten(), 0.0)

        return trajectory

    # -------------------------------------------------------------------------
    # HARVESTING STRATEGIES
    # -------------------------------------------------------------------------

    def uniform_sustainable_harvest_fraction(self) -> float:
        """
        Compute the theoretical uniform harvest fraction h* that maintains
        a stationary population:
        x_{k+1} = (1 - h) * L * x_k
        For stationarity: (1 - h) * lambda_1 = 1  =>  h* = 1 - 1 / lambda_1.

        Returns
        -------
        float
            Sustainable harvest fraction h* in [0, 1), or 0.0 if lambda_1 <= 1.
        """
        lam = self.dominant_eigenvalue
        if lam > 1.0:
            return float(1.0 - 1.0 / lam)
        return 0.0

    def simulate_uniform_harvesting(
        self,
        x0: Union[List[float], np.ndarray],
        harvest_fraction: float,
        steps: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate Uniform Harvesting where a constant fraction h of all age classes
        is harvested immediately after reproduction:
        x_{k+1} = (1 - h) * L * x_k.
        Harvest yield at step k: Y_k = h * (L * x_k).

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (trajectory, yield_history)
        """
        if not (0.0 <= harvest_fraction <= 1.0):
            raise ValueError(f"Harvest fraction must be in [0.0, 1.0], received {harvest_fraction}.")

        x_curr = np.array(x0, dtype=np.float64).flatten()
        trajectory = np.zeros((steps + 1, self.n_classes), dtype=np.float64)
        yield_history = np.zeros((steps, self.n_classes), dtype=np.float64)
        trajectory[0, :] = x_curr

        eff_matrix = (1.0 - harvest_fraction) * self.matrix
        for k in range(steps):
            produced = self.matrix @ x_curr
            yield_k = harvest_fraction * produced
            x_next = (1.0 - harvest_fraction) * produced
            x_curr = np.maximum(x_next, 0.0)
            trajectory[k + 1, :] = x_curr
            yield_history[k, :] = np.maximum(yield_k, 0.0)

        return trajectory, yield_history

    def simulate_proportional_harvesting(
        self,
        x0: Union[List[float], np.ndarray],
        harvest_fractions: Union[List[float], np.ndarray],
        steps: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate Stage-Specific / Proportional Harvesting:
        H = diag(h_1, h_2, ..., h_n)
        x_{k+1} = (I - H) * L * x_k
        Harvest yield at step k: Y_k = H * (L * x_k).

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (trajectory, yield_history)
        """
        h_vec = np.array(harvest_fractions, dtype=np.float64).flatten()
        if len(h_vec) != self.n_classes:
            raise ValueError(f"Harvest fraction vector length ({len(h_vec)}) != {self.n_classes}.")
        if np.any(h_vec < 0.0) or np.any(h_vec > 1.0):
            raise ValueError("All stage harvest fractions must lie in [0.0, 1.0].")

        h_mat = np.diag(h_vec)
        i_minus_h = np.eye(self.n_classes) - h_mat
        harvested_matrix = i_minus_h @ self.matrix

        x_curr = np.array(x0, dtype=np.float64).flatten()
        trajectory = np.zeros((steps + 1, self.n_classes), dtype=np.float64)
        yield_history = np.zeros((steps, self.n_classes), dtype=np.float64)
        trajectory[0, :] = x_curr

        for k in range(steps):
            produced = self.matrix @ x_curr
            yield_k = h_mat @ produced
            x_next = harvested_matrix @ x_curr
            x_curr = np.maximum(x_next, 0.0)
            trajectory[k + 1, :] = x_curr
            yield_history[k, :] = np.maximum(yield_k, 0.0)

        return trajectory, yield_history

    def simulate_constant_quota_harvesting(
        self,
        x0: Union[List[float], np.ndarray],
        quota_vector: Union[List[float], np.ndarray],
        steps: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate Constant Quota Harvesting:
        Fixed absolute number of individuals harvested each period:
        x_{k+1} = L * x_k - h_quota.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (trajectory, actual_yield_history)
        """
        quota = np.array(quota_vector, dtype=np.float64).flatten()
        if len(quota) != self.n_classes:
            raise ValueError(f"Quota vector length ({len(quota)}) != {self.n_classes}.")
        if np.any(quota < 0.0):
            raise ValueError("Harvest quotas cannot be negative.")

        x_curr = np.array(x0, dtype=np.float64).flatten()
        trajectory = np.zeros((steps + 1, self.n_classes), dtype=np.float64)
        actual_yield = np.zeros((steps, self.n_classes), dtype=np.float64)
        trajectory[0, :] = x_curr

        for k in range(steps):
            unharvested = self.matrix @ x_curr
            # Harvest can never exceed available stock
            harvested = np.minimum(unharvested, quota)
            x_next = np.maximum(unharvested - quota, 0.0)
            x_curr = x_next
            trajectory[k + 1, :] = x_curr
            actual_yield[k, :] = harvested

        return trajectory, actual_yield

    def solve_equilibrium_quota(
        self,
        target_equilibrium: Union[List[float], np.ndarray],
    ) -> Tuple[np.ndarray, bool]:
        """
        Solve for the constant quota vector h that maintains a target equilibrium x*:
        x* = L * x* - h  <=>  (L - I) * x* = h.

        Parameters
        ----------
        target_equilibrium : Union[List[float], np.ndarray]
            Desired stationary population vector x* >= 0.

        Returns
        -------
        Tuple[np.ndarray, bool]
            (sustainable_quota, is_sustainable)
            is_sustainable is True if all components of quota h are strictly non-negative.
        """
        x_star = np.array(target_equilibrium, dtype=np.float64).flatten()
        if len(x_star) != self.n_classes:
            raise ValueError(f"Target equilibrium length ({len(x_star)}) != {self.n_classes}.")

        # h = (L - I) * x*
        l_minus_i = self.matrix - np.eye(self.n_classes)
        quota = l_minus_i @ x_star

        is_sustainable = bool(np.all(quota >= -1e-9))
        quota = np.maximum(quota, 0.0)
        return quota, is_sustainable

    def get_summary_metrics(self) -> Dict[str, Union[float, int, str, bool]]:
        """Return comprehensive mathematical metrics of the matrix model."""
        return {
            "species_name": self.species_name,
            "age_classes": self.n_classes,
            "dominant_eigenvalue": round(self.dominant_eigenvalue, 5),
            "intrinsic_growth_rate": round(self.intrinsic_growth_rate, 5),
            "net_reproductive_rate": round(self.net_reproductive_rate, 5),
            "generation_time_years": round(self.generation_time, 2),
            "damping_ratio": round(self.damping_ratio, 4),
            "is_primitive": self.is_primitive(),
            "is_diagonalizable": bool(self._is_diagonalizable),
            "uniform_sustainable_harvest_pct": round(
                self.uniform_sustainable_harvest_fraction() * 100.0, 2
            ),
        }
