"""
BioHarvest-Sim: Stochastic Simulations & Sensitivity Engine
===========================================================
Author: Applied Mathematician & Software Architect
Standard: ISO/IEC/IEEE 12207 & 27001, PEP-8 Compliant

Implements:
- Monte Carlo Population Viability Analysis (PVA)
- Environmental Stochasticity (vital rate perturbations)
- Catastrophic Disaster Shock Modeling (droughts, epizootic outbreaks)
- Quasi-Extinction Probability & Time-to-Extinction Distribution
- Caswell Sensitivity & Elasticity Perturbation Profiling
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from core.math_engine import LeslieMatrixEngine


class MonteCarloSimulator:
    """
    Monte Carlo stochastic engine modeling demographic uncertainty,
    environmental fluctuations, and catastrophe shocks on age-structured populations.
    """

    def __init__(
        self,
        engine: LeslieMatrixEngine,
        random_seed: Optional[int] = 42,
    ) -> None:
        """
        Initialize the simulator with a base Leslie matrix engine.

        Parameters
        ----------
        engine : LeslieMatrixEngine
            Base population matrix model.
        random_seed : Optional[int]
            RNG seed for deterministic reproducibility.
        """
        self.engine = engine
        self.rng = np.random.default_rng(random_seed)
        self.n = engine.n_classes

    def run_simulation(
        self,
        x0: Union[List[float], np.ndarray],
        years: int = 50,
        num_iterations: int = 500,
        fecundity_cv: float = 0.15,
        survival_cv: float = 0.08,
        catastrophe_prob: float = 0.04,
        catastrophe_impact: float = 0.40,
        quasi_extinction_threshold: Optional[float] = None,
        harvest_fraction: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Execute Monte Carlo population viability trajectories.

        Parameters
        ----------
        x0 : Union[List[float], np.ndarray]
            Initial population distribution vector.
        years : int
            Projection duration in years (time steps).
        num_iterations : int
            Number of stochastic Monte Carlo realization paths.
        fecundity_cv : float
            Coefficient of variation (std / mean) for environmental fecundity noise.
        survival_cv : float
            Coefficient of variation for survival probability fluctuations.
        catastrophe_prob : float
            Annual probability of a severe environmental disaster (e.g. drought/epidemic).
        catastrophe_impact : float
            Proportional reduction in survival/reproduction during a disaster year (0 to 1).
        quasi_extinction_threshold : Optional[float]
            Population threshold below which the population is deemed functionally extinct.
            Defaults to 10% of initial total population or 20 individuals, whichever is larger.
        harvest_fraction : float
            Uniform post-reproduction harvest fraction applied each year.

        Returns
        -------
        Dict[str, Any]
            Dictionary with trajectory statistics, extinction probability, and percentiles.
        """
        x0_arr = np.array(x0, dtype=np.float64).flatten()
        init_total = float(np.sum(x0_arr))

        if quasi_extinction_threshold is None:
            quasi_extinction_threshold = max(20.0, 0.10 * init_total)

        base_f = self.engine.fecundity.copy()
        base_s = self.engine.survival.copy()

        # Array of trajectories: [iteration, year, age_class]
        trajectories = np.zeros((num_iterations, years + 1, self.n), dtype=np.float64)
        trajectories[:, 0, :] = x0_arr

        # Array of total population sizes: [iteration, year]
        total_populations = np.zeros((num_iterations, years + 1), dtype=np.float64)
        total_populations[:, 0] = init_total

        extinction_years = []
        is_extinct = np.zeros(num_iterations, dtype=bool)

        for it in range(num_iterations):
            x_t = x0_arr.copy()
            extinct_this_run = False

            for yr in range(1, years + 1):
                # 1. Environmental stochasticity on vital rates
                f_noise = self.rng.normal(0.0, fecundity_cv, size=self.n)
                # Lognormal multiplier with mean ~ 1.0
                f_pert = base_f * np.exp(f_noise - 0.5 * (fecundity_cv ** 2))
                f_pert = np.maximum(f_pert, 0.0)

                s_noise = self.rng.normal(0.0, survival_cv * base_s, size=self.n - 1)
                s_pert = np.clip(base_s + s_noise, 0.001, 0.999)

                # 2. Catastrophe Shock
                if self.rng.random() < catastrophe_prob:
                    f_pert *= (1.0 - catastrophe_impact)
                    s_pert *= (1.0 - catastrophe_impact)

                # 3. Assemble stochastic Leslie matrix
                l_stochastic = np.zeros((self.n, self.n), dtype=np.float64)
                l_stochastic[0, :] = f_pert
                for idx in range(self.n - 1):
                    l_stochastic[idx + 1, idx] = s_pert[idx]

                # 4. Step forward and apply harvesting
                x_next = l_stochastic @ x_t
                if harvest_fraction > 0.0:
                    x_next = (1.0 - harvest_fraction) * x_next

                x_t = np.maximum(x_next, 0.0)
                tot_pop = float(np.sum(x_t))

                trajectories[it, yr, :] = x_t
                total_populations[it, yr] = tot_pop

                # Check quasi-extinction
                if tot_pop < quasi_extinction_threshold and not extinct_this_run:
                    extinct_this_run = True
                    extinction_years.append(yr)

            is_extinct[it] = extinct_this_run

        extinction_risk = float(np.mean(is_extinct))
        mean_time_to_extinction = (
            float(np.mean(extinction_years)) if extinction_years else None
        )

        # Calculate time-series percentiles across iterations
        p5 = np.percentile(total_populations, 5, axis=0)
        p25 = np.percentile(total_populations, 25, axis=0)
        p50 = np.percentile(total_populations, 50, axis=0)  # Median
        p75 = np.percentile(total_populations, 75, axis=0)
        p95 = np.percentile(total_populations, 95, axis=0)
        mean_pop = np.mean(total_populations, axis=0)

        years_axis = np.arange(years + 1)

        return {
            "years": years_axis,
            "num_iterations": num_iterations,
            "initial_population": init_total,
            "quasi_extinction_threshold": quasi_extinction_threshold,
            "extinction_risk": extinction_risk,
            "extinction_count": int(np.sum(is_extinct)),
            "mean_time_to_extinction": mean_time_to_extinction,
            "percentiles": {
                "p5": p5,
                "p25": p25,
                "median": p50,
                "p75": p75,
                "p95": p95,
                "mean": mean_pop,
            },
            "sample_trajectories": total_populations[: min(25, num_iterations), :],
            "terminal_population_median": float(p50[-1]),
        }


class SensitivityAnalyzer:
    """
    Caswell perturbation sensitivity and elasticity analyzer for identifying
    ecologically critical life stages and vital rate vulnerabilities.
    """

    def __init__(self, engine: LeslieMatrixEngine) -> None:
        """Initialize with a configured LeslieMatrixEngine."""
        self.engine = engine

    def get_vital_rates_sensitivity_dataframe(self) -> pd.DataFrame:
        """
        Construct a structured DataFrame of vital rates, their sensitivities,
        and their elasticities to lambda_1.
        """
        s_mat = self.engine.compute_sensitivity_matrix()
        e_mat = self.engine.compute_elasticity_matrix()
        n = self.engine.n_classes

        records = []

        # Fecundities (row 0 of Leslie matrix)
        for j in range(n):
            records.append({
                "Parameter Type": "Fecundity",
                "Age Class": f"Class {j+1}",
                "Base Value": round(float(self.engine.fecundity[j]), 4),
                "Sensitivity (dλ/df)": round(float(s_mat[0, j]), 5),
                "Elasticity (% contribution)": round(float(e_mat[0, j]) * 100.0, 3),
            })

        # Survival probabilities (subdiagonal of Leslie matrix)
        for i in range(n - 1):
            records.append({
                "Parameter Type": "Survival",
                "Age Class": f"Class {i+1} -> {i+2}",
                "Base Value": round(float(self.engine.survival[i]), 4),
                "Sensitivity (dλ/ds)": round(float(s_mat[i + 1, i]), 5),
                "Elasticity (% contribution)": round(float(e_mat[i + 1, i]) * 100.0, 3),
            })

        df = pd.DataFrame(records)
        df = df.sort_values(by="Elasticity (% contribution)", ascending=False).reset_index(drop=True)
        return df
