"""
BioHarvest-Sim: Matrix-Based Population Dynamics & Sustainable Yield Optimization System
========================================================================================
Main Orchestrator & CLI / GUI Entry Point
Author: Applied Mathematician & Software Architect
Standard: ISO/IEC/IEEE 12207 & 27001, PEP-8 Compliant
"""

import argparse
import os
import subprocess
import sys
from typing import Optional
import numpy as np

from core.math_engine import LeslieMatrixEngine
from core.optimizer import MSYOptimizer
from analytics.simulations import MonteCarloSimulator, SensitivityAnalyzer
from analytics.exporter import ReportExporter
from gui.presets import SPECIES_PRESETS, get_preset_names, get_species_preset


def run_cli_demo(species_name: Optional[str] = None, export_artifacts: bool = True) -> None:
    """
    Run an end-to-end mathematical analysis and simulation pipeline via CLI.

    Parameters
    ----------
    species_name : Optional[str]
        Specific preset to run, or None to run all presets.
    export_artifacts : bool
        Whether to generate PDF reports and CSV/JSON files.
    """
    targets = [species_name] if species_name else get_preset_names()

    print("=" * 80)
    print("BIOHARVEST-SIM: MATHEMATICAL POPULATION DYNAMICS & MSY OPTIMIZATION SYSTEM")
    print("Linear Algebra Core | ISO/IEC/IEEE 12207 Compliant")
    print("=" * 80)

    # Ensure UTF-8 output on Windows console
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    for name in targets:
        print(f"\n>>> ANALYZING SPECIES: {name}")
        preset = get_species_preset(name)

        # 1. Initialize Engine
        engine = LeslieMatrixEngine(
            fecundity=preset["fecundity"],
            survival=preset["survival"],
            species_name=name.split(" (")[0],
        )

        metrics = engine.get_summary_metrics()
        print(f"  * Age Classes (N)               : {metrics['age_classes']}")
        print(f"  * Dominant Eigenvalue (lambda_1): {metrics['dominant_eigenvalue']:.5f}")
        print(f"  * Intrinsic Growth Rate (r)     : {metrics['intrinsic_growth_rate']:.5f} yr^-1")
        print(f"  * Net Reproductive Rate (R_0)   : {metrics['net_reproductive_rate']:.5f}")
        print(f"  * Mean Generation Time (T_c)    : {metrics['generation_time_years']:.2f} years")
        print(f"  * Damping Ratio (lambda_1/|l2|) : {metrics['damping_ratio']:.4f}")
        print(f"  * Perron-Frobenius Primitivity  : {metrics['is_primitive']}")
        print(f"  * Uniform Sustainable Harvest h*: {metrics['uniform_sustainable_harvest_pct']:.2f}%")

        # Stable Age Distribution
        w = engine.stable_age_distribution
        w_str = ", ".join([f"{val*100:.1f}%" for val in w])
        print(f"  * Stable Age Distribution (w)   : [{w_str}]")

        # 2. MSY Linear Programming Optimization
        optimizer = MSYOptimizer(engine)
        lp_res = optimizer.optimize_linear_programming_msy(
            carrying_capacity=preset.get("carrying_capacity", 1000),
            economic_weights=preset.get("economic_weights"),
            harvest_timing="post_reproduction",
        )

        if lp_res["success"]:
            print(f"  * MSY Total Annual Yield        : {lp_res['total_yield']:.2f} individuals")
            print(f"  * MSY Total Economic Valuation  : ${lp_res['economic_value']:,.2f}")
            h_opt = lp_res["optimal_harvest"]
            print(f"  * MSY Harvest Vector (h*)       : {np.round(h_opt, 1)}")
        else:
            print(f"  * MSY Optimization Status       : {lp_res['message']}")

        # 3. Monte Carlo Viability Analysis
        simulator = MonteCarloSimulator(engine, random_seed=42)
        x0 = np.array(preset["initial_population"], dtype=np.float64)
        mc_res = simulator.run_simulation(
            x0=x0,
            years=preset.get("default_time_steps", 40),
            num_iterations=200,
            harvest_fraction=engine.uniform_sustainable_harvest_fraction(),
        )
        print(f"  * 50-Year Extinction Probability: {mc_res['extinction_risk']*100:.1f}%")

        # 4. Export Artifacts
        if export_artifacts:
            exporter = ReportExporter(engine)
            clean_name = name.split(" (")[0].replace(" ", "_")
            pdf_file = f"BioHarvest_{clean_name}_Report.pdf"
            json_file = f"BioHarvest_{clean_name}_Telemetry.json"
            csv_file = f"BioHarvest_{clean_name}_Trajectories.csv"

            exporter.generate_pdf_report(
                filepath=pdf_file,
                initial_population=x0,
                time_steps=preset.get("default_time_steps", 40),
                msy_results=lp_res,
                monte_carlo_results=mc_res,
            )
            exporter.export_json_telemetry(lp_res, mc_res, json_file)

            steps = preset.get("default_time_steps", 40)
            traj_none = engine.fast_predict_trajectory(x0, steps)
            traj_sust, _ = engine.simulate_uniform_harvesting(
                x0, engine.uniform_sustainable_harvest_fraction(), steps
            )
            exporter.export_csv_trajectory(
                steps,
                {"No_Harvest": traj_none, "Sustainable_Uniform": traj_sust},
                csv_file,
            )
            print(f"  * Generated Artifacts           : {pdf_file}, {json_file}, {csv_file}")

    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
    print("=" * 80)


def launch_gui() -> None:
    """Launch the Streamlit interactive GUI."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "gui", "dashboard.py")
    cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path]
    print(f"Launching BioHarvest-Sim GUI via Streamlit: {' '.join(cmd)}")
    subprocess.run(cmd)


def main() -> None:
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(
        description="BioHarvest-Sim: Matrix-Based Population Dynamics & Sustainable Yield Optimization System"
    )
    parser.add_argument(
        "--gui", action="store_true", help="Launch interactive Streamlit web dashboard"
    )
    parser.add_argument(
        "--species",
        type=str,
        default=None,
        help="Run CLI analysis for a specific species (e.g. 'Fin Whale', 'Pacific Salmon')",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Disable automatic generation of PDF, CSV, and JSON artifacts in CLI mode",
    )
    parser.add_argument(
        "--test", action="store_true", help="Execute automated unit test suite"
    )

    args = parser.parse_args()

    if args.gui:
        launch_gui()
    elif args.test:
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir="tests", pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        # Default behavior: run CLI demonstration
        run_cli_demo(species_name=args.species, export_artifacts=not args.no_export)


if __name__ == "__main__":
    main()
