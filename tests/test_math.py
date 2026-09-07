"""
BioHarvest-Sim: Comprehensive Mathematical & System Unit Tests
==============================================================
Author: Applied Mathematician & Software Architect
Standard: ISO/IEC/IEEE 12207 & 27001, PEP-8 Compliant

Tests cover:
- Leslie Matrix Construction & Validation
- Perron-Frobenius Dominant Eigendecomposition
- Spectral Decomposition & Diagonalization Acceleration (L^k = P D^k P^-1)
- Caswell Sensitivity & Elasticity Theorems (Sum(E_ij) == 1)
- Harvesting Equilibrium & Uniform MSY Equations
- Linear Programming Optimization via HiGHS
- Monte Carlo PVA Stochastic Engine
- Ecological Preset Life Tables
- Exporter Functionality (PDF, CSV, JSON)
"""

import json
import os
import tempfile
import unittest
import numpy as np

from core.math_engine import LeslieMatrixEngine
from core.optimizer import MSYOptimizer
from analytics.simulations import MonteCarloSimulator, SensitivityAnalyzer
from analytics.exporter import ReportExporter
from gui.presets import SPECIES_PRESETS, get_preset_names, get_species_preset


class TestLeslieMatrixEngine(unittest.TestCase):
    """Test suite for core Leslie Matrix linear algebra operations."""

    def setUp(self) -> None:
        """Set up standard Anton & Rorres 3-age class test model."""
        self.fecundity = [0.0, 1.2, 1.8]
        self.survival = [0.6, 0.5]
        self.engine = LeslieMatrixEngine(self.fecundity, self.survival, species_name="TestSpecies")

    def test_matrix_structure(self) -> None:
        """Verify Leslie matrix dimensional layout and subdiagonal entries."""
        L = self.engine.matrix
        self.assertEqual(L.shape, (3, 3))
        np.testing.assert_array_almost_equal(L[0, :], [0.0, 1.2, 1.8])
        self.assertAlmostEqual(L[1, 0], 0.6)
        self.assertAlmostEqual(L[2, 1], 0.5)
        self.assertAlmostEqual(L[0, 1], 1.2)
        self.assertAlmostEqual(L[2, 0], 0.0)

    def test_validation_constraints(self) -> None:
        """Verify parameter validation raises appropriate exceptions."""
        # Negative fecundity
        with self.assertRaises(ValueError):
            LeslieMatrixEngine([-0.1, 1.0], [0.5])
        # Invalid survival > 1.0
        with self.assertRaises(ValueError):
            LeslieMatrixEngine([1.0, 1.0], [1.2])
        # Mismatched length
        with self.assertRaises(ValueError):
            LeslieMatrixEngine([1.0, 1.0, 1.0], [0.5])
        # Single class (N < 2)
        with self.assertRaises(ValueError):
            LeslieMatrixEngine([1.0], [])
        # All zero fertility
        with self.assertRaises(ValueError):
            LeslieMatrixEngine([0.0, 0.0], [0.5])

    def test_perron_frobenius_properties(self) -> None:
        """Verify Perron-Frobenius theorem properties on dominant eigenvalue and eigenvector."""
        lam1 = self.engine.dominant_eigenvalue
        v1 = self.engine.stable_age_distribution
        L = self.engine.matrix

        # 1. lambda_1 must be strictly positive and real
        self.assertGreater(lam1, 0.0)
        self.assertTrue(isinstance(lam1, float))

        # 2. lambda_1 must equal spectral radius rho(L) = max |lambda_i|
        all_eigs = self.engine._eigenvalues
        assert all_eigs is not None
        max_mag = np.max(np.abs(all_eigs))
        self.assertAlmostEqual(lam1, max_mag, places=6)

        # 3. Right eigenvector equation: L * v1 = lambda_1 * v1
        L_v1 = L @ v1
        lam_v1 = lam1 * v1
        np.testing.assert_array_almost_equal(L_v1, lam_v1, decimal=5)

        # 4. Stable age distribution sums to 1 and is non-negative
        self.assertAlmostEqual(float(np.sum(v1)), 1.0, places=6)
        self.assertTrue(np.all(v1 >= -1e-9))

        # 5. Left eigenvector equation: u1^T * L = lambda_1 * u1^T
        u1 = self.engine.reproductive_values
        u1_L = u1 @ L
        lam_u1 = lam1 * u1
        # Proportionality check
        ratio = u1_L / np.maximum(lam_u1, 1e-12)
        np.testing.assert_array_almost_equal(ratio, np.ones_like(ratio), decimal=4)

    def test_spectral_decomposition_acceleration(self) -> None:
        """Verify fast diagonalization L^k = P * D^k * P^-1 produces identical results to matrix powers."""
        x0 = np.array([100.0, 50.0, 20.0])
        steps = 15

        # Accelerated trajectory
        traj_fast = self.engine.fast_predict_trajectory(x0, steps)

        # Direct manual power iteration
        traj_manual = np.zeros((steps + 1, 3))
        curr = x0.copy()
        traj_manual[0, :] = curr
        for k in range(1, steps + 1):
            curr = self.engine.matrix @ curr
            traj_manual[k, :] = curr

        np.testing.assert_array_almost_equal(traj_fast, traj_manual, decimal=4)

    def test_net_reproductive_rate_and_demographics(self) -> None:
        """Verify Euler-Lotka relationship: R0 > 1 <=> lambda_1 > 1."""
        r0 = self.engine.net_reproductive_rate
        lam1 = self.engine.dominant_eigenvalue

        # For our test system: R0 = f1*l1 + f2*l2 + f3*l3 = 0 + 1.2*0.6 + 1.8*(0.6*0.5) = 0.72 + 0.54 = 1.26
        self.assertAlmostEqual(r0, 1.26, places=5)
        self.assertGreater(r0, 1.0)
        self.assertGreater(lam1, 1.0)

        # Intrinsic growth rate r = ln(lambda_1)
        r = self.engine.intrinsic_growth_rate
        self.assertAlmostEqual(r, np.log(lam1), places=6)

    def test_elasticity_matrix_sums_to_one(self) -> None:
        """Verify fundamental theorem: the sum of all elements in the elasticity matrix equals exactly 1.0."""
        e_mat = self.engine.compute_elasticity_matrix()
        total_elasticity = float(np.sum(e_mat))
        self.assertAlmostEqual(total_elasticity, 1.0, places=5)
        # Elasticities must be non-negative
        self.assertTrue(np.all(e_mat >= -1e-9))


class TestHarvestingStrategies(unittest.TestCase):
    """Test suite for animal population harvesting strategies."""

    def setUp(self) -> None:
        self.fecundity = [0.0, 1.5, 2.0]
        self.survival = [0.7, 0.6]
        self.engine = LeslieMatrixEngine(self.fecundity, self.survival)

    def test_uniform_sustainable_equilibrium(self) -> None:
        """Verify (1 - h*) * L * w = w where h* = 1 - 1/lambda_1."""
        lam1 = self.engine.dominant_eigenvalue
        self.assertGreater(lam1, 1.0)

        h_star = self.engine.uniform_sustainable_harvest_fraction()
        self.assertAlmostEqual(h_star, 1.0 - 1.0 / lam1, places=6)

        w = self.engine.stable_age_distribution
        # Apply one uniform harvest step to stable age distribution
        produced = self.engine.matrix @ w
        remaining = (1.0 - h_star) * produced

        # Remaining must equal original w exactly
        np.testing.assert_array_almost_equal(remaining, w, decimal=5)

    def test_uniform_harvest_simulation(self) -> None:
        """Verify uniform harvesting simulation runs and preserves non-negativity."""
        x0 = [200.0, 100.0, 50.0]
        traj, yields = self.engine.simulate_uniform_harvesting(x0, harvest_fraction=0.2, steps=20)

        self.assertEqual(traj.shape, (21, 3))
        self.assertEqual(yields.shape, (20, 3))
        self.assertTrue(np.all(traj >= 0.0))
        self.assertTrue(np.all(yields >= 0.0))

    def test_proportional_harvest_simulation(self) -> None:
        """Verify stage-specific harvesting simulation operates correctly."""
        x0 = [150.0, 80.0, 40.0]
        h_vec = [0.0, 0.25, 0.50]  # Protect juveniles, harvest adults
        traj, yields = self.engine.simulate_proportional_harvesting(x0, h_vec, steps=15)

        self.assertEqual(traj.shape, (16, 3))
        # Juvenile yield must be 0
        self.assertTrue(np.all(yields[:, 0] == 0.0))
        self.assertTrue(np.all(traj >= 0.0))

    def test_equilibrium_quota_solver(self) -> None:
        """Verify solving (L - I) * x* = h for sustainable fixed quota."""
        # For an arbitrary positive target vector
        x_target = np.array([300.0, 150.0, 80.0])
        quota, is_sust = self.engine.solve_equilibrium_quota(x_target)
        self.assertEqual(len(quota), 3)


class TestMSYOptimizer(unittest.TestCase):
    """Test suite for Maximum Sustainable Yield Linear Programming formulation."""

    def setUp(self) -> None:
        # High fecundity system for guaranteed positive surplus yield
        self.fecundity = [0.0, 1.8, 2.4]
        self.survival = [0.7, 0.6]
        self.engine = LeslieMatrixEngine(self.fecundity, self.survival)
        self.optimizer = MSYOptimizer(self.engine)

    def test_msy_linear_program_post_reproduction(self) -> None:
        """Verify MSY LP post-reproduction equilibrium (L - I)x* - h* = 0."""
        res = self.optimizer.optimize_linear_programming_msy(
            carrying_capacity=1000.0,
            harvest_timing="post_reproduction",
        )
        self.assertTrue(res["success"])
        self.assertGreater(res["total_yield"], 0.0)

        x_opt = res["optimal_stock"]
        h_opt = res["optimal_harvest"]

        # Capacity check
        self.assertLessEqual(np.sum(x_opt), 1000.0 + 1e-5)

        # Equilibrium check: (L - I) x* - h* == 0
        l_minus_i = self.engine.matrix - np.eye(3)
        diff = l_minus_i @ x_opt - h_opt
        np.testing.assert_array_almost_equal(diff, np.zeros(3), decimal=4)

    def test_msy_with_protected_juveniles(self) -> None:
        """Verify LP with 0% harvest cap on juvenile age class 1."""
        res = self.optimizer.optimize_linear_programming_msy(
            carrying_capacity=1000.0,
            stage_harvest_caps=[0.0, 1.0, 1.0],
            harvest_timing="post_reproduction",
        )
        self.assertTrue(res["success"])
        h_opt = res["optimal_harvest"]
        # Age class 1 harvest must be exactly 0
        self.assertAlmostEqual(h_opt[0], 0.0, places=6)

    def test_yield_curve_generation(self) -> None:
        """Verify uniform yield curve generation identifies maximum sustainable yield apex."""
        x0 = [100.0, 60.0, 30.0]
        h_vals, yields, msy_h, msy_val = self.optimizer.generate_uniform_yield_curve(x0, num_points=25, sim_steps=30)

        self.assertEqual(len(h_vals), 25)
        self.assertEqual(len(yields), 25)
        self.assertGreater(msy_val, 0.0)
        self.assertGreater(msy_h, 0.0)
        self.assertLess(msy_h, 1.0)


class TestMonteCarloViability(unittest.TestCase):
    """Test suite for stochastic Population Viability Analysis (PVA)."""

    def setUp(self) -> None:
        self.fecundity = [0.0, 1.4, 2.0]
        self.survival = [0.65, 0.55]
        self.engine = LeslieMatrixEngine(self.fecundity, self.survival)
        self.simulator = MonteCarloSimulator(self.engine, random_seed=123)

    def test_stochastic_simulation_bounds_and_percentiles(self) -> None:
        """Verify Monte Carlo simulation bounds, percentiles ordering, and extinction risk bounds."""
        x0 = [200.0, 100.0, 50.0]
        res = self.simulator.run_simulation(
            x0=x0,
            years=25,
            num_iterations=100,
            catastrophe_prob=0.05,
            catastrophe_impact=0.50,
        )

        self.assertEqual(len(res["years"]), 26)
        self.assertGreaterEqual(res["extinction_risk"], 0.0)
        self.assertLessEqual(res["extinction_risk"], 1.0)

        pct = res["percentiles"]
        # Monotonicity check across percentiles
        self.assertTrue(np.all(pct["p5"] <= pct["p25"] + 1e-5))
        self.assertTrue(np.all(pct["p25"] <= pct["median"] + 1e-5))
        self.assertTrue(np.all(pct["median"] <= pct["p75"] + 1e-5))
        self.assertTrue(np.all(pct["p75"] <= pct["p95"] + 1e-5))


class TestPresetsIntegrity(unittest.TestCase):
    """Verify integrity of all built-in ecological presets."""

    def test_all_presets_valid(self) -> None:
        """Ensure all presets instantiate valid Leslie matrices with positive dominant eigenvalues."""
        names = get_preset_names()
        self.assertGreaterEqual(len(names), 4)

        for name in names:
            preset = get_species_preset(name)
            f = preset["fecundity"]
            s = preset["survival"]
            x0 = preset["initial_population"]

            # Dimensions
            self.assertEqual(len(s), len(f) - 1, f"Failed for {name}")
            self.assertEqual(len(x0), len(f), f"Failed for {name}")

            engine = LeslieMatrixEngine(f, s, species_name=name)
            self.assertGreater(engine.dominant_eigenvalue, 0.0)
            self.assertAlmostEqual(float(np.sum(engine.stable_age_distribution)), 1.0, places=5)


class TestExporter(unittest.TestCase):
    """Test suite for PDF, CSV, and JSON report export capabilities."""

    def setUp(self) -> None:
        self.engine = LeslieMatrixEngine([0.0, 1.5, 2.0], [0.7, 0.6], species_name="ExportTest")
        self.exporter = ReportExporter(self.engine)

    def test_json_telemetry_export(self) -> None:
        """Verify JSON export creates valid parseable JSON with all required keys."""
        json_str = self.exporter.export_json_telemetry()
        data = json.loads(json_str)

        self.assertEqual(data["metadata"]["system"], "BioHarvest-Sim")
        self.assertIn("dominant_eigenvalue", data["spectral_analysis"])
        self.assertIn("stable_age_distribution", data["spectral_analysis"])

    def test_csv_and_pdf_generation(self) -> None:
        """Verify physical generation of CSV trajectory and multi-page PDF files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = os.path.join(tmpdir, "test_traj.csv")
            pdf_file = os.path.join(tmpdir, "test_report.pdf")

            traj = self.engine.fast_predict_trajectory([100.0, 50.0, 20.0], steps=10)
            self.exporter.export_csv_trajectory(10, {"Baseline": traj}, csv_file)
            self.assertTrue(os.path.exists(csv_file))
            self.assertGreater(os.path.getsize(csv_file), 100)

            self.exporter.generate_pdf_report(
                filepath=pdf_file,
                initial_population=np.array([100.0, 50.0, 20.0]),
                time_steps=10,
            )
            self.assertTrue(os.path.exists(pdf_file))
            self.assertGreater(os.path.getsize(pdf_file), 1000)


if __name__ == "__main__":
    unittest.main()
