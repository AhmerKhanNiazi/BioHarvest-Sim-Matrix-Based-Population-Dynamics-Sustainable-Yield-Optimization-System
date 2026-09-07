"""
BioHarvest-Sim: Data Exporter & PDF Analytical Report Generator
==============================================================
Author: Applied Mathematician & Software Architect
Standard: ISO/IEC/IEEE 12207 & 27001, PEP-8 Compliant

Generates:
- Multi-page comprehensive analytical PDF report using matplotlib PdfPages
- Structured JSON model telemetry and audit logs
- CSV tabular trajectory time series for external statistical software (R, SPSS, Excel)
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless server environments
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

from core.math_engine import LeslieMatrixEngine


class ReportExporter:
    """
    Enterprise data and document exporter producing publication-ready PDF reports,
    CSV telemetry streams, and JSON analytical summaries.
    """

    def __init__(self, engine: LeslieMatrixEngine) -> None:
        """Initialize exporter with a configured LeslieMatrixEngine."""
        self.engine = engine

    def export_csv_trajectory(
        self,
        time_steps: int,
        trajectories: Dict[str, np.ndarray],
        filepath: str,
        age_class_labels: Optional[List[str]] = None,
    ) -> str:
        """
        Export simulation trajectories across scenarios to a tidy CSV file.

        Parameters
        ----------
        time_steps : int
            Number of projected steps.
        trajectories : Dict[str, np.ndarray]
            Mapping scenario_name -> (steps + 1) x N population trajectory array.
        filepath : str
            Output file path.
        age_class_labels : Optional[List[str]]
            Labels for age classes.

        Returns
        -------
        str
            Destination filepath.
        """
        n = self.engine.n_classes
        if age_class_labels is None:
            age_class_labels = [f"Age_Class_{i+1}" for i in range(n)]

        rows = []
        for scenario, traj in trajectories.items():
            for t in range(traj.shape[0]):
                row = {
                    "Scenario": scenario,
                    "Time_Step": t,
                    "Total_Population": float(np.sum(traj[t, :])),
                }
                for i in range(n):
                    row[age_class_labels[i]] = float(traj[t, i])
                rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False)
        return filepath

    def export_json_telemetry(
        self,
        msy_results: Optional[Dict[str, Any]] = None,
        monte_carlo_results: Optional[Dict[str, Any]] = None,
        filepath: Optional[str] = None,
    ) -> str:
        """
        Serialize complete system parameters, spectral invariants, MSY optimization,
        and Monte Carlo risk metrics into a structured JSON string / file.

        Returns
        -------
        str
            JSON string or path to exported file.
        """
        metrics = self.engine.get_summary_metrics()

        telemetry = {
            "metadata": {
                "system": "BioHarvest-Sim",
                "version": "1.0.0",
                "timestamp_utc": datetime.utcnow().isoformat(),
                "species": self.engine.species_name,
            },
            "parameters": {
                "age_classes": self.engine.n_classes,
                "fecundity": self.engine.fecundity.tolist(),
                "survival": self.engine.survival.tolist(),
                "leslie_matrix": self.engine.matrix.tolist(),
            },
            "spectral_analysis": {
                "dominant_eigenvalue": metrics["dominant_eigenvalue"],
                "intrinsic_growth_rate": metrics["intrinsic_growth_rate"],
                "net_reproductive_rate": metrics["net_reproductive_rate"],
                "generation_time": metrics["generation_time_years"],
                "damping_ratio": metrics["damping_ratio"],
                "is_primitive": metrics["is_primitive"],
                "is_diagonalizable": metrics["is_diagonalizable"],
                "stable_age_distribution": self.engine.stable_age_distribution.tolist(),
                "reproductive_values": self.engine.reproductive_values.tolist(),
            },
            "harvesting_invariants": {
                "uniform_sustainable_harvest_pct": metrics["uniform_sustainable_harvest_pct"],
            },
        }

        if msy_results is not None:
            telemetry["msy_optimization"] = {
                "success": msy_results.get("success", False),
                "total_yield": float(msy_results.get("total_yield", 0.0)),
                "economic_value": float(msy_results.get("economic_value", 0.0)),
                "optimal_stock": [float(x) for x in msy_results.get("optimal_stock", [])],
                "optimal_harvest": [float(h) for h in msy_results.get("optimal_harvest", [])],
            }

        if monte_carlo_results is not None:
            telemetry["monte_carlo_risk"] = {
                "iterations": monte_carlo_results.get("num_iterations"),
                "extinction_risk_probability": float(monte_carlo_results.get("extinction_risk", 0.0)),
                "quasi_extinction_threshold": float(monte_carlo_results.get("quasi_extinction_threshold", 0.0)),
                "mean_time_to_extinction": monte_carlo_results.get("mean_time_to_extinction"),
            }

        json_str = json.dumps(telemetry, indent=2)
        if filepath is not None:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_str)
            return filepath
        return json_str

    def generate_pdf_report(
        self,
        filepath: str,
        initial_population: np.ndarray,
        time_steps: int = 40,
        msy_results: Optional[Dict[str, Any]] = None,
        monte_carlo_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a multi-page publication-grade PDF report with analytical commentary,
        formal mathematical tables, eigen-spectrum plots, and harvest trajectory graphs.
        """
        # Styling parameters
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        with PdfPages(filepath) as pdf:
            # -------------------------------------------------------------
            # PAGE 1: Title, Executive Summary & Demographics Table
            # -------------------------------------------------------------
            fig1, ax1 = plt.subplots(figsize=(8.5, 11))
            ax1.axis("off")

            # Header Banner
            fig1.text(0.5, 0.94, "BioHarvest-Sim: Analytical Assessment Report",
                      ha="center", fontsize=18, fontweight="bold", color="#1E3A8A")
            fig1.text(0.5, 0.91, f"Species: {self.engine.species_name} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                      ha="center", fontsize=10, color="#4B5563")
            fig1.text(0.5, 0.885, "ISO/IEC/IEEE 12207 Compliance | High-Precision Linear Algebra Core",
                      ha="center", fontsize=8, fontstyle="italic", color="#6B7280")

            # Executive Summary Box
            summary_text = (
                f"EXECUTIVE SUMMARY:\n"
                f"This report details the demographic stability and sustainable yield optimization for "
                f"'{self.engine.species_name}' based on discrete-time Leslie matrix theory. "
                f"The population exhibits a dominant eigenvalue $\\lambda_1$ = {self.engine.dominant_eigenvalue:.4f}, "
                f"corresponding to an intrinsic growth rate of r = {self.engine.intrinsic_growth_rate:.4f} per year. "
                f"The net reproductive rate $R_0$ is {self.engine.net_reproductive_rate:.4f} with a mean generation time of "
                f"{self.engine.generation_time:.2f} years. The theoretical maximum uniform sustainable harvest fraction is "
                f"{self.engine.uniform_sustainable_harvest_fraction()*100:.2f}% per annum."
            )
            ax1.text(0.08, 0.76, summary_text, fontsize=9.5, va="top", wrap=True,
                     bbox=dict(boxstyle="round,pad=0.6", facecolor="#EFF6FF", edgecolor="#3B82F6", alpha=0.9))

            # Demographic Metrics Table
            metrics = self.engine.get_summary_metrics()
            table_data = [
                ["Age Classes (N)", str(metrics["age_classes"])],
                ["Dominant Eigenvalue ($\lambda_1$)", f"{metrics['dominant_eigenvalue']:.5f}"],
                ["Intrinsic Growth Rate (r = ln $\lambda_1$)", f"{metrics['intrinsic_growth_rate']:.5f} yr^-1"],
                ["Net Reproductive Rate ($R_0$)", f"{metrics['net_reproductive_rate']:.5f}"],
                ["Mean Generation Time (Tc)", f"{metrics['generation_time_years']:.2f} years"],
                ["Damping Ratio ($\lambda_1$ / |$\lambda_2$|)", f"{metrics['damping_ratio']:.4f}"],
                ["Perron-Frobenius Primitivity", "Verified Primitive" if metrics["is_primitive"] else "Imprimitive / Cyclic"],
                ["Matrix Diagonalizable", "Yes (L = P D P^-1)" if metrics["is_diagonalizable"] else "Defective"],
                ["Uniform Sustainable Harvest (h*)", f"{metrics['uniform_sustainable_harvest_pct']:.2f}% per step"],
            ]
            table = ax1.table(cellText=table_data, colLabels=["Demographic Parameter", "Value"],
                              loc="center", cellLoc="left", colWidths=[0.55, 0.35], bbox=[0.08, 0.40, 0.84, 0.30])
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            for (row, col), cell in table.get_celld().items():
                if row == 0:
                    cell.set_facecolor("#1E3A8A")
                    cell.set_text_props(color="white", weight="bold")
                elif row % 2 == 0:
                    cell.set_facecolor("#F9FAFB")

            # Leslie Matrix Representation (Formatted sample or full)
            mat_str = np.array2string(self.engine.matrix, precision=3, suppress_small=True, max_line_width=80)
            ax1.text(0.08, 0.34, "Leslie Projection Matrix (L):", fontsize=10, fontweight="bold", color="#1F2937")
            ax1.text(0.08, 0.32, mat_str, fontsize=7.5, family="monospace", va="top",
                     bbox=dict(boxstyle="square,pad=0.5", facecolor="#F3F4F6", edgecolor="#D1D5DB"))

            pdf.savefig(fig1, bbox_inches="tight")
            plt.close(fig1)

            # -------------------------------------------------------------
            # PAGE 2: Spectral Properties & Age Distributions
            # -------------------------------------------------------------
            fig2, (ax_spec, ax_dist) = plt.subplots(1, 2, figsize=(11, 5.5))

            # Eigen-spectrum in Complex Plane
            lambdas = self.engine._eigenvalues
            if lambdas is not None:
                theta = np.linspace(0, 2 * np.pi, 200)
                ax_spec.plot(np.cos(theta), np.sin(theta), "r--", linewidth=1.2, label="Unit Circle (|λ| = 1)")
                ax_spec.scatter(np.real(lambdas), np.imag(lambdas), color="#3B82F6", s=60, edgecolors="navy", zorder=4, label="Eigenvalues")
                # Highlight dominant
                dom_val = self.engine.dominant_eigenvalue
                ax_spec.scatter([dom_val], [0], color="#EF4444", s=120, edgecolors="darkred", zorder=5, label=f"Dominant $\\lambda_1$ ({dom_val:.3f})")
                ax_spec.axhline(0, color="gray", linewidth=0.6)
                ax_spec.axvline(0, color="gray", linewidth=0.6)
                ax_spec.set_title("Eigen-Spectrum (Complex Plane)", fontsize=11, fontweight="bold", color="#1E3A8A")
                ax_spec.set_xlabel("Real Part (Re)", fontsize=9)
                ax_spec.set_ylabel("Imaginary Part (Im)", fontsize=9)
                ax_spec.set_aspect("equal", "datalim")
                ax_spec.legend(fontsize=8, loc="upper left")

            # Stable Age Distribution vs Reproductive Values
            age_labels = [f"Age {i+1}" for i in range(self.engine.n_classes)]
            x_pos = np.arange(len(age_labels))
            w = self.engine.stable_age_distribution
            u = self.engine.reproductive_values
            # Normalize u to sum to 1 for visual comparison
            u_norm = u / np.sum(u) if np.sum(u) > 0 else u

            width = 0.38
            ax_dist.bar(x_pos - width / 2, w, width, label="Stable Age Dist (w)", color="#10B981", alpha=0.85)
            ax_dist.bar(x_pos + width / 2, u_norm, width, label="Reproductive Value (u)", color="#6366F1", alpha=0.85)
            ax_dist.set_title("Stable Distribution vs. Reproductive Value", fontsize=11, fontweight="bold", color="#1E3A8A")
            ax_dist.set_xticks(x_pos)
            ax_dist.set_xticklabels(age_labels, rotation=45, ha="right", fontsize=8)
            ax_dist.set_ylabel("Normalized Proportion", fontsize=9)
            ax_dist.legend(fontsize=8)

            fig2.suptitle("Spectral Decomposition & Asymptotic Age Structure", fontsize=13, fontweight="bold", color="#1E3A8A")
            pdf.savefig(fig2, bbox_inches="tight")
            plt.close(fig2)

            # -------------------------------------------------------------
            # PAGE 3: Harvesting Regimes & Trajectories
            # -------------------------------------------------------------
            fig3, (ax_traj, ax_msy) = plt.subplots(1, 2, figsize=(11, 5.5))

            # Trajectory Comparisons: No Harvest vs Sustainable Harvest vs Over-Harvest
            steps = time_steps
            t_axis = np.arange(steps + 1)
            traj_noharvest = self.engine.fast_predict_trajectory(initial_population, steps)
            tot_noharvest = np.sum(traj_noharvest, axis=1)

            h_sust = self.engine.uniform_sustainable_harvest_fraction()
            traj_sust, _ = self.engine.simulate_uniform_harvesting(initial_population, h_sust, steps)
            tot_sust = np.sum(traj_sust, axis=1)

            h_over = min(0.95, h_sust * 1.5 if h_sust > 0 else 0.15)
            traj_over, _ = self.engine.simulate_uniform_harvesting(initial_population, h_over, steps)
            tot_over = np.sum(traj_over, axis=1)

            ax_traj.plot(t_axis, tot_noharvest, color="#3B82F6", linewidth=2.0, label="No Harvest (h = 0)")
            ax_traj.plot(t_axis, tot_sust, color="#10B981", linewidth=2.2, linestyle="--", label=f"Sustainable (h = {h_sust*100:.1f}%)")
            ax_traj.plot(t_axis, tot_over, color="#EF4444", linewidth=2.0, linestyle=":", label=f"Over-Harvest (h = {h_over*100:.1f}%)")
            ax_traj.set_title("Population Trajectory Comparison", fontsize=11, fontweight="bold", color="#1E3A8A")
            ax_traj.set_xlabel("Time Step (Years)", fontsize=9)
            ax_traj.set_ylabel("Total Population Size", fontsize=9)
            ax_traj.legend(fontsize=8)

            # MSY Quota Breakdown (Bar chart of optimal harvest by stage)
            if msy_results is not None and msy_results.get("success", False):
                h_opt = msy_results["optimal_harvest"]
                x_opt = msy_results["optimal_stock"]
                x_indices = np.arange(len(h_opt))
                ax_msy.bar(x_indices - 0.18, x_opt, 0.36, label="Equilibrium Stock (x*)", color="#3B82F6", alpha=0.8)
                ax_msy.bar(x_indices + 0.18, h_opt, 0.36, label="Optimal Harvest Quota (h*)", color="#F59E0B", alpha=0.85)
                ax_msy.set_xticks(x_indices)
                ax_msy.set_xticklabels([f"Age {i+1}" for i in x_indices], rotation=45, ha="right", fontsize=8)
                ax_msy.set_title(f"MSY Linear Program Solved (Yield: {msy_results['total_yield']:.1f})",
                                 fontsize=11, fontweight="bold", color="#1E3A8A")
                ax_msy.set_ylabel("Number of Individuals", fontsize=9)
                ax_msy.legend(fontsize=8)
            else:
                ax_msy.text(0.5, 0.5, "MSY Linear Program not provided", ha="center", va="center", color="gray")

            fig3.suptitle("Harvest Dynamics & Optimization", fontsize=13, fontweight="bold", color="#1E3A8A")
            pdf.savefig(fig3, bbox_inches="tight")
            plt.close(fig3)

            # -------------------------------------------------------------
            # PAGE 4: Monte Carlo Risk & Sensitivity Analysis
            # -------------------------------------------------------------
            fig4, (ax_mc, ax_sens) = plt.subplots(1, 2, figsize=(11, 5.5))

            if monte_carlo_results is not None:
                mc_yrs = monte_carlo_results["years"]
                pct = monte_carlo_results["percentiles"]
                ax_mc.fill_between(mc_yrs, pct["p5"], pct["p95"], color="#3B82F6", alpha=0.15, label="5th - 95th Percentile")
                ax_mc.fill_between(mc_yrs, pct["p25"], pct["p75"], color="#3B82F6", alpha=0.30, label="25th - 75th Percentile")
                ax_mc.plot(mc_yrs, pct["median"], color="#1E3A8A", linewidth=2.0, label="Median Trajectory")
                thresh = monte_carlo_results["quasi_extinction_threshold"]
                ax_mc.axhline(thresh, color="red", linestyle="--", linewidth=1.2, label=f"Extinction Threshold ({thresh:.0f})")
                ax_mc.set_title(f"Monte Carlo Extinction Risk ({monte_carlo_results['extinction_risk']*100:.1f}%)",
                                fontsize=11, fontweight="bold", color="#1E3A8A")
                ax_mc.set_xlabel("Projection Year", fontsize=9)
                ax_mc.set_ylabel("Population Size", fontsize=9)
                ax_mc.legend(fontsize=7.5, loc="upper right")
            else:
                ax_mc.text(0.5, 0.5, "Monte Carlo PVA not provided", ha="center", va="center", color="gray")

            # Sensitivity / Elasticity Horizontal Bar
            e_mat = self.engine.compute_elasticity_matrix()
            e_fec = np.sum(e_mat[0, :])
            e_surv = np.sum(e_mat[1:, :]) if self.engine.n_classes > 1 else 0.0
            categories = ["Reproduction (Fecundity)", "Survival (Transitions)"]
            vals = [e_fec * 100.0, e_surv * 100.0]
            colors = ["#F59E0B", "#10B981"]

            ax_sens.barh(categories, vals, color=colors, height=0.5)
            ax_sens.set_xlim(0, 100)
            for i, v in enumerate(vals):
                ax_sens.text(v + 2, i, f"{v:.1f}%", va="center", fontweight="bold", fontsize=9)
            ax_sens.set_title("Elasticity Contribution to Growth ($\lambda_1$)", fontsize=11, fontweight="bold", color="#1E3A8A")
            ax_sens.set_xlabel("Elasticity Percentage (%)", fontsize=9)

            fig4.suptitle("Environmental Stochasticity & Vital Rate Elasticities", fontsize=13, fontweight="bold", color="#1E3A8A")
            pdf.savefig(fig4, bbox_inches="tight")
            plt.close(fig4)

        return filepath
