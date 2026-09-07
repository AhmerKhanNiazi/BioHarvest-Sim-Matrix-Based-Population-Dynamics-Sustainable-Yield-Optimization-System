"""
BioHarvest-Sim: Maximum Sustainable Yield (MSY) Optimizer
=========================================================
Author: Applied Mathematician & Software Architect
Standard: ISO/IEC/IEEE 12207 & 27001, PEP-8 Compliant

Formulates and solves the Maximum Sustainable Yield (MSY) Linear Program
using scipy.optimize.linprog with the HiGHS modern simplex / interior-point solver.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.optimize import linprog

from core.math_engine import LeslieMatrixEngine


class MSYOptimizer:
    """
    Formulates and optimizes age-structured population harvesting models
    to determine Maximum Sustainable Yield (MSY) and optimal stage-specific quotas.
    """

    def __init__(self, engine: LeslieMatrixEngine) -> None:
        """
        Initialize the MSY Optimizer with a configured LeslieMatrixEngine.

        Parameters
        ----------
        engine : LeslieMatrixEngine
            Instantiated mathematical engine containing the population Leslie matrix.
        """
        self.engine = engine
        self.L = engine.matrix
        self.n = engine.n_classes

    def optimize_linear_programming_msy(
        self,
        carrying_capacity: float = 1000.0,
        economic_weights: Optional[Union[List[float], np.ndarray]] = None,
        harvest_timing: str = "post_reproduction",
        stage_harvest_caps: Optional[Union[List[float], np.ndarray]] = None,
    ) -> Dict[str, Union[float, np.ndarray, str, bool]]:
        """
        Solve the Linear Program for Maximum Sustainable Yield.

        Decision vector: z = [x_1, ..., x_n, h_1, ..., h_n]^T in R^{2n}
        where x is standing stock and h is sustainable harvest vector.

        Parameters
        ----------
        carrying_capacity : float
            Total standing stock capacity constraint: sum(x_i) <= carrying_capacity.
        economic_weights : Optional[Union[List[float], np.ndarray]]
            Value per individual in each age class (default: 1.0 for all classes).
        harvest_timing : str
            "post_reproduction" : x* = L * x* - h  <=>  (L - I) x* - h = 0
            "pre_reproduction"  : x* = L * (x* - h) <=>  (I - L) x* + L h = 0
        stage_harvest_caps : Optional[Union[List[float], np.ndarray]]
            Maximum allowable harvest fraction per class (e.g. 0 for protected juveniles).

        Returns
        -------
        Dict[str, Union[float, np.ndarray, str, bool]]
            Dictionary containing optimization status, optimal stock x*,
            optimal harvest h*, total yield, and economic valuation.
        """
        n = self.n

        # Objective: Maximize c^T * h  <=>  Minimize [ 0_{1xn}, -c^T ] * z
        if economic_weights is None:
            c = np.ones(n, dtype=np.float64)
        else:
            c = np.array(economic_weights, dtype=np.float64).flatten()
            if len(c) != n:
                raise ValueError(f"Economic weights length ({len(c)}) must match age classes ({n}).")

        obj_cost = np.concatenate([np.zeros(n), -c])

        # Equality Constraints: A_eq * z = b_eq
        if harvest_timing == "post_reproduction":
            # (L - I) * x - h = 0
            l_minus_i = self.L - np.eye(n)
            minus_i = -np.eye(n)
            a_eq = np.hstack([l_minus_i, minus_i])
            b_eq = np.zeros(n)
        elif harvest_timing == "pre_reproduction":
            # (I - L) * x + L * h = 0
            i_minus_l = np.eye(n) - self.L
            a_eq = np.hstack([i_minus_l, self.L])
            b_eq = np.zeros(n)
        else:
            raise ValueError(
                f"Unknown harvest timing '{harvest_timing}'. Choose 'post_reproduction' or 'pre_reproduction'."
            )

        # Inequality Constraints: A_ub * z <= b_ub
        # 1. Carrying capacity: sum(x_i) <= K
        cap_row = np.concatenate([np.ones(n), np.zeros(n)])

        # 2. Harvest cannot exceed stock: h_i <= alpha_i * x_i  <=>  -alpha_i * x_i + h_i <= 0
        if stage_harvest_caps is not None:
            alphas = np.array(stage_harvest_caps, dtype=np.float64).flatten()
            if len(alphas) != n:
                raise ValueError(f"Stage harvest caps length ({len(alphas)}) != {n}.")
            alpha_diag = np.diag(alphas)
        else:
            alpha_diag = np.eye(n)

        stock_limit_mat = np.hstack([-alpha_diag, np.eye(n)])

        a_ub = np.vstack([cap_row, stock_limit_mat])
        b_ub = np.concatenate([[carrying_capacity], np.zeros(n)])

        # Variable bounds: x_i >= 0, h_i >= 0
        bounds = [(0.0, None) for _ in range(2 * n)]

        # Solve Linear Program using HiGHS
        res = linprog(
            c=obj_cost,
            A_ub=a_ub,
            b_ub=b_ub,
            A_eq=a_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs",
        )

        if res.success:
            z_opt = res.x
            x_opt = z_opt[:n]
            h_opt = z_opt[n:]
            # Clean numerical precision
            x_opt = np.maximum(x_opt, 0.0)
            h_opt = np.maximum(h_opt, 0.0)
            total_yield = float(np.sum(h_opt))
            economic_val = float(np.dot(c, h_opt))
            harvest_fractions = np.zeros(n)
            non_zero_stock = x_opt > 1e-6
            harvest_fractions[non_zero_stock] = (
                h_opt[non_zero_stock] / x_opt[non_zero_stock]
            )

            return {
                "success": True,
                "message": res.message,
                "optimal_stock": x_opt,
                "optimal_harvest": h_opt,
                "harvest_fractions": harvest_fractions,
                "total_yield": total_yield,
                "economic_value": economic_val,
                "carrying_capacity_used": float(np.sum(x_opt)),
                "harvest_timing": harvest_timing,
            }
        else:
            return {
                "success": False,
                "message": res.message,
                "optimal_stock": np.zeros(n),
                "optimal_harvest": np.zeros(n),
                "harvest_fractions": np.zeros(n),
                "total_yield": 0.0,
                "economic_value": 0.0,
                "carrying_capacity_used": 0.0,
                "harvest_timing": harvest_timing,
            }

    def generate_uniform_yield_curve(
        self,
        x0: Union[List[float], np.ndarray],
        num_points: int = 50,
        sim_steps: int = 60,
    ) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """
        Generate Yield vs. Harvest Fraction (h) curve for uniform harvesting.

        Parameters
        ----------
        x0 : Union[List[float], np.ndarray]
            Initial population distribution.
        num_points : int
            Number of points along h in [0, 1].
        sim_steps : int
            Simulation steps to reach quasi-steady state.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, float, float]
            (h_values, steady_yields, msy_harvest_rate, msy_yield)
        """
        h_values = np.linspace(0.0, 0.95, num_points)
        yields = np.zeros(num_points)

        for i, h in enumerate(h_values):
            _, yield_hist = self.engine.simulate_uniform_harvesting(
                x0=x0, harvest_fraction=float(h), steps=sim_steps
            )
            # Equilibrium yield is the average over the final 10 steps
            yields[i] = float(np.mean(np.sum(yield_hist[-10:, :], axis=1)))

        max_idx = int(np.argmax(yields))
        msy_h = float(h_values[max_idx])
        msy_yield = float(yields[max_idx])

        return h_values, yields, msy_h, msy_yield
