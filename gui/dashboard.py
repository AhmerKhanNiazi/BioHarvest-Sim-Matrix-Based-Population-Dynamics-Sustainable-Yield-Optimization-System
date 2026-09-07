"""
BioHarvest-Sim: Interactive Computational Dashboard
===================================================
Author: Applied Mathematician & Software Architect
Standard: ISO/IEC/IEEE 12207 & 27001, PEP-8 Compliant

Streamlit-based dashboard featuring:
- Real-time parameter tuning (Leslie matrices, vital rates)
- Plotly 3D population surface and phase portraits
- Complex plane eigen-spectrum visualizer
- MSY Linear Programming optimization
- Monte Carlo Population Viability & Extinction Risk Analysis
- Multi-format data and report export (PDF, CSV, JSON)
"""

import io
import os
import sys
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.math_engine import LeslieMatrixEngine
from core.optimizer import MSYOptimizer
from analytics.simulations import MonteCarloSimulator, SensitivityAnalyzer
from analytics.exporter import ReportExporter
from gui.presets import SPECIES_PRESETS, get_preset_names, get_species_preset


def setup_page_config() -> None:
    """Configure Streamlit page layout, title, and dark-mode styling."""
    st.set_page_config(
        page_title="BioHarvest-Sim | Matrix Population Dynamics & MSY",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom styling enhancements
    st.markdown(
        """
        <style>
        .metric-card {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .metric-title {
            color: #94A3B8;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        .metric-value {
            color: #38BDF8;
            font-size: 1.6rem;
            font-weight: 700;
        }
        .metric-sub {
            color: #64748B;
            font-size: 0.75rem;
            margin-top: 4px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> Dict:
    """Render sidebar controls and parameter selection."""
    st.sidebar.title("🧬 BioHarvest-Sim")
    st.sidebar.markdown("**Matrix Population Dynamics & MSY**")
    st.sidebar.markdown("---")

    # Preset selection
    presets = get_preset_names()
    preset_choice = st.sidebar.selectbox(
        "Ecological Species Preset",
        presets + ["Custom Population Model"],
        index=0,
    )

    if preset_choice != "Custom Population Model":
        preset = get_species_preset(preset_choice)
        st.sidebar.caption(preset["description"])
        n_classes = len(preset["fecundity"])
        fecundity_init = preset["fecundity"]
        survival_init = preset["survival"]
        init_pop = preset["initial_population"]
        default_steps = preset.get("default_time_steps", 40)
        carrying_capacity = preset.get("carrying_capacity", 2500)
        economic_weights = preset.get("economic_weights", [1.0] * n_classes)
        species_label = preset_choice.split(" (")[0]
    else:
        species_label = st.sidebar.text_input("Species Name", value="Custom Species")
        n_classes = st.sidebar.slider("Number of Age Classes (N)", min_value=2, max_value=12, value=4)
        fecundity_init = [0.0] * (n_classes - 1) + [2.5]
        survival_init = [0.8] * (n_classes - 1)
        init_pop = [100.0] * n_classes
        default_steps = 40
        carrying_capacity = 2000
        economic_weights = [1.0] * n_classes

    st.sidebar.markdown("### ⚙️ Vital Rates Editor")

    # Vital rate sliders in an expander
    with st.sidebar.expander("Edit Fecundity & Survival", expanded=(preset_choice == "Custom Population Model")):
        fecundity = []
        for i in range(n_classes):
            val = st.number_input(
                f"Fecundity f_{i+1} (Age {i+1})",
                min_value=0.0,
                max_value=5000.0,
                value=float(fecundity_init[i]),
                step=0.05,
                key=f"fec_{i}",
            )
            fecundity.append(val)

        survival = []
        for i in range(n_classes - 1):
            val = st.slider(
                f"Survival s_{i+1} (Age {i+1} -> {i+2})",
                min_value=0.001,
                max_value=0.999,
                value=float(min(0.999, max(0.001, survival_init[i]))),
                step=0.01,
                key=f"surv_{i}",
            )
            survival.append(val)

    # Initial Population
    with st.sidebar.expander("Initial Population Vector (x₀)", expanded=False):
        population = []
        for i in range(n_classes):
            pop_val = st.number_input(
                f"Initial Count Age {i+1}",
                min_value=0.0,
                max_value=1e7,
                value=float(init_pop[i]),
                step=10.0,
                key=f"pop_{i}",
            )
            population.append(pop_val)

    st.sidebar.markdown("### ⏱️ Simulation Controls")
    time_steps = st.sidebar.slider("Projection Time Horizon (Years)", min_value=10, max_value=100, value=default_steps, step=5)
    capacity = st.sidebar.number_input("Carrying Capacity (K)", min_value=100, max_value=1000000, value=int(carrying_capacity), step=500)

    return {
        "species_name": species_label,
        "n_classes": n_classes,
        "fecundity": fecundity,
        "survival": survival,
        "population": population,
        "time_steps": time_steps,
        "carrying_capacity": capacity,
        "economic_weights": economic_weights,
    }


def render_metric_header(engine: LeslieMatrixEngine) -> None:
    """Render high-level Linear Algebra demographic KPI cards."""
    metrics = engine.get_summary_metrics()
    lam = engine.dominant_eigenvalue
    r = engine.intrinsic_growth_rate
    r0 = engine.net_reproductive_rate
    tc = engine.generation_time
    rho = engine.damping_ratio
    h_opt = engine.uniform_sustainable_harvest_fraction()

    status_color = "#10B981" if lam > 1.0001 else ("#EF4444" if lam < 0.9999 else "#F59E0B")
    status_label = "Growing (λ > 1)" if lam > 1.0001 else ("Declining (λ < 1)" if lam < 0.9999 else "Stationary (λ = 1)")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Dominant Eigenvalue</div>
                <div class="metric-value" style="color: {status_color};">λ₁ = {lam:.4f}</div>
                <div class="metric-sub">{status_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Intrinsic Growth Rate</div>
                <div class="metric-value">r = {r:.4f}</div>
                <div class="metric-sub">r = ln(λ₁) yr⁻¹</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Net Reproductive Rate</div>
                <div class="metric-value">R₀ = {r0:.3f}</div>
                <div class="metric-sub">Mean Lifetime Offspring</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Generation Time</div>
                <div class="metric-value">T_c = {tc:.1f}y</div>
                <div class="metric-sub">Mean Mother Childbirth Age</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col5:
        rho_str = f"{rho:.2f}" if np.isfinite(rho) else "∞"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Damping Ratio</div>
                <div class="metric-value">ρ = {rho_str}</div>
                <div class="metric-sub">λ₁ / |λ₂| (Convergence)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col6:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Uniform MSY Yield</div>
                <div class="metric-value" style="color: #F59E0B;">h* = {h_opt*100:.1f}%</div>
                <div class="metric-sub">1 - 1/λ₁ Equilibrium</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    """Main Streamlit execution loop."""
    setup_page_config()
    params = render_sidebar()

    # Build mathematical core engine
    try:
        engine = LeslieMatrixEngine(
            fecundity=params["fecundity"],
            survival=params["survival"],
            species_name=params["species_name"],
        )
    except Exception as e:
        st.error(f"⚠️ Model Initialization Error: {str(e)}")
        st.stop()

    # Display KPI header
    render_metric_header(engine)
    st.markdown("<br>", unsafe_allow_html=True)

    # Multi-tab layout
    tabs = st.tabs([
        "📈 3D Dynamics & Trajectories",
        "🔮 Spectral Analysis & Age Structure",
        "🎯 MSY & Harvesting Optimization",
        "🌀 Phase Space Portrait",
        "🎲 Monte Carlo Risk & PVA",
        "📑 Reports & Data Export",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: 3D DYNAMICS & TRAJECTORIES
    # -------------------------------------------------------------------------
    with tabs[0]:
        st.subheader("Population Trajectory Simulation & 3D Manifold")

        c1, c2 = st.columns([1, 1])

        # Baseline trajectories
        steps = params["time_steps"]
        x0 = np.array(params["population"], dtype=np.float64)

        # Scenarios
        h_sust = engine.uniform_sustainable_harvest_fraction()
        h_over = min(0.95, h_sust * 1.5 if h_sust > 0 else 0.20)

        traj_none = engine.fast_predict_trajectory(x0, steps)
        traj_sust, yield_sust = engine.simulate_uniform_harvesting(x0, h_sust, steps)
        traj_over, yield_over = engine.simulate_uniform_harvesting(x0, h_over, steps)

        t_axis = np.arange(steps + 1)

        with c1:
            # 2D Multi-scenario plot
            fig_traj = go.Figure()
            fig_traj.add_trace(go.Scatter(
                x=t_axis, y=np.sum(traj_none, axis=1),
                name="No Harvesting (h = 0)", line=dict(color="#38BDF8", width=2.5)
            ))
            fig_traj.add_trace(go.Scatter(
                x=t_axis, y=np.sum(traj_sust, axis=1),
                name=f"Sustainable Uniform (h = {h_sust*100:.1f}%)",
                line=dict(color="#10B981", width=2.5, dash="dash")
            ))
            fig_traj.add_trace(go.Scatter(
                x=t_axis, y=np.sum(traj_over, axis=1),
                name=f"Over-Harvesting (h = {h_over*100:.1f}%)",
                line=dict(color="#EF4444", width=2.5, dash="dot")
            ))
            fig_traj.update_layout(
                title="Scenario Comparison: Total Population Trajectory",
                xaxis_title="Time Horizon (Years)",
                yaxis_title="Total Population Size",
                template="plotly_dark",
                legend=dict(x=0.02, y=0.98),
                margin=dict(l=40, r=40, t=50, b=40),
            )
            st.plotly_chart(fig_traj, use_container_width=True)

        with c2:
            # 3D Population Surface: Time (X) vs Age Class (Y) vs Population (Z)
            age_classes_axis = [f"Age {i+1}" for i in range(engine.n_classes)]
            z_surface = traj_none.T  # Shape: (N, steps + 1)

            fig_3d = go.Figure(data=[go.Surface(
                z=z_surface,
                x=t_axis,
                y=np.arange(engine.n_classes),
                colorscale="Viridis",
                colorbar=dict(title="Count"),
            )])
            fig_3d.update_layout(
                title="3D Population Surface (No Harvest)",
                scene=dict(
                    xaxis_title="Time (Years)",
                    yaxis=dict(title="Age Class", tickvals=list(range(engine.n_classes)), ticktext=age_classes_axis),
                    zaxis_title="Population Count",
                ),
                template="plotly_dark",
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig_3d, use_container_width=True)

        # Detailed age class breakdown chart
        st.markdown("#### Dynamic Cohort Progression Over Time")
        fig_cohort = go.Figure()
        colors = px.colors.qualitative.Plotly
        for i in range(engine.n_classes):
            fig_cohort.add_trace(go.Scatter(
                x=t_axis, y=traj_none[:, i],
                name=f"Age Class {i+1}",
                line=dict(color=colors[i % len(colors)], width=2),
                mode="lines+markers" if steps <= 30 else "lines",
            ))
        fig_cohort.update_layout(
            title="Age-Specific Cohort Sizes Under Natural Dynamics",
            xaxis_title="Time Step (Years)",
            yaxis_title="Abundance",
            template="plotly_dark",
            legend=dict(orientation="h", y=-0.2),
            margin=dict(l=40, r=40, t=50, b=40),
        )
        st.plotly_chart(fig_cohort, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 2: SPECTRAL ANALYSIS & AGE STRUCTURE
    # -------------------------------------------------------------------------
    with tabs[1]:
        st.subheader("Spectral Eigendecomposition & Perron-Frobenius Properties")

        col_spec1, col_spec2 = st.columns([1, 1])

        with col_spec1:
            # Complex plane eigen-spectrum with unit circle
            lambdas = engine._eigenvalues
            if lambdas is not None:
                fig_spec = go.Figure()

                # Unit circle
                theta = np.linspace(0, 2 * np.pi, 300)
                fig_spec.add_trace(go.Scatter(
                    x=np.cos(theta), y=np.sin(theta),
                    mode="lines", name="Unit Circle (|λ| = 1)",
                    line=dict(color="rgba(239, 68, 68, 0.6)", dash="dash", width=1.5)
                ))

                # Eigenvalues
                fig_spec.add_trace(go.Scatter(
                    x=np.real(lambdas), y=np.imag(lambdas),
                    mode="markers", name="Subdominant Eigenvalues",
                    marker=dict(size=12, color="#38BDF8", symbol="circle", line=dict(width=1, color="white")),
                    text=[f"λ_{i+1}: {l.real:.3f} + {l.imag:.3f}j (|λ|={abs(l):.3f})" for i, l in enumerate(lambdas)],
                    hoverinfo="text",
                ))

                # Highlight dominant
                dom_val = engine.dominant_eigenvalue
                fig_spec.add_trace(go.Scatter(
                    x=[dom_val], y=[0],
                    mode="markers+text", name=f"Dominant λ₁ = {dom_val:.4f}",
                    marker=dict(size=16, color="#F59E0B", symbol="star"),
                    text=[f"λ₁ = {dom_val:.3f}"], textposition="top right",
                ))

                fig_spec.update_layout(
                    title="Eigen-Spectrum in the Complex Plane",
                    xaxis_title="Real Axis (Re)",
                    yaxis_title="Imaginary Axis (Im)",
                    template="plotly_dark",
                    yaxis=dict(scaleanchor="x", scaleratio=1),
                    margin=dict(l=40, r=40, t=50, b=40),
                )
                st.plotly_chart(fig_spec, use_container_width=True)

        with col_spec2:
            # Stable Age Distribution vs Reproductive Value
            w_stable = engine.stable_age_distribution
            u_rep = engine.reproductive_values
            u_norm = u_rep / np.sum(u_rep) if np.sum(u_rep) > 0 else u_rep
            age_labels = [f"Class {i+1}" for i in range(engine.n_classes)]

            fig_dist = go.Figure()
            fig_dist.add_trace(go.Bar(
                x=age_labels, y=w_stable,
                name="Stable Age Distribution (w)", marker_color="#10B981"
            ))
            fig_dist.add_trace(go.Bar(
                x=age_labels, y=u_norm,
                name="Reproductive Value (u)", marker_color="#6366F1"
            ))
            fig_dist.update_layout(
                title="Stable Age Structure vs. Reproductive Value (Fisher)",
                barmode="group",
                xaxis_title="Age Class",
                yaxis_title="Normalized Proportion",
                template="plotly_dark",
                margin=dict(l=40, r=40, t=50, b=40),
            )
            st.plotly_chart(fig_dist, use_container_width=True)

        # Mathematical Proof & Matrix Display
        with st.expander("📐 Formal Mathematical Formulations & Leslie Matrix", expanded=False):
            st.markdown(r"""
            **Perron-Frobenius Theorem Context:**
            For an irreducible, non-negative Leslie matrix $L$, there exists a unique strictly positive eigenvalue $\lambda_1 = \rho(L)$
            that equals the spectral radius, associated with a strictly positive right eigenvector $v_1 > 0$:
            $$L v_1 = \lambda_1 v_1, \quad u_1^T L = \lambda_1 u_1^T$$
            **Diagonalization & Accelerated Power Iteration:**
            $$L = P D P^{-1} \implies x_k = L^k x_0 = P D^k P^{-1} x_0$$
            """)
            st.dataframe(pd.DataFrame(
                engine.matrix,
                columns=[f"Age {i+1}" for i in range(engine.n_classes)],
                index=[f"Age {i+1}" for i in range(engine.n_classes)],
            ))

    # -------------------------------------------------------------------------
    # TAB 3: MSY & HARVESTING OPTIMIZATION
    # -------------------------------------------------------------------------
    with tabs[2]:
        st.subheader("Maximum Sustainable Yield (MSY) Optimization")

        optimizer = MSYOptimizer(engine)

        col_msy_ctrl, col_msy_chart = st.columns([1, 2])

        with col_msy_ctrl:
            st.markdown("#### LP Solver Configuration")
            timing = st.radio(
                "Harvest Timing",
                ["post_reproduction", "pre_reproduction"],
                format_func=lambda x: "Post-Reproduction (L x* - h = x*)" if x == "post_reproduction" else "Pre-Reproduction (L(x* - h) = x*)",
            )
            cap_limit = float(params["carrying_capacity"])

            protect_juveniles = st.checkbox("Protect Juveniles (0% Harvest on Age 1)", value=False)
            caps = None
            if protect_juveniles:
                caps = [0.0] + [1.0] * (engine.n_classes - 1)

            opt_res = optimizer.optimize_linear_programming_msy(
                carrying_capacity=cap_limit,
                economic_weights=params.get("economic_weights"),
                harvest_timing=timing,
                stage_harvest_caps=caps,
            )

            if opt_res["success"]:
                st.success("✅ Optimal MSY Equilibrium Found!")
                st.metric("Total Sustainable Annual Yield", f"{opt_res['total_yield']:.1f} individuals/yr")
                st.metric("Total Economic Valuation", f"${opt_res['economic_value']:,.2f}")
                st.metric("Equilibrium Stock Maintained", f"{opt_res['carrying_capacity_used']:.1f}")
            else:
                st.error(f"Optimization Unfeasible: {opt_res['message']}")

        with col_msy_chart:
            # Optimal Quota vs Standing Stock Bar Chart
            if opt_res["success"]:
                age_idx = [f"Age {i+1}" for i in range(engine.n_classes)]
                fig_opt = go.Figure()
                fig_opt.add_trace(go.Bar(
                    x=age_idx, y=opt_res["optimal_stock"],
                    name="Equilibrium Standing Stock (x*)", marker_color="#38BDF8"
                ))
                fig_opt.add_trace(go.Bar(
                    x=age_idx, y=opt_res["optimal_harvest"],
                    name="Sustainable Harvest Quota (h*)", marker_color="#F59E0B"
                ))
                fig_opt.update_layout(
                    title="Linear Programming MSY: Optimal Stock vs. Harvest Quota",
                    barmode="group",
                    xaxis_title="Age Class",
                    yaxis_title="Abundance",
                    template="plotly_dark",
                    margin=dict(l=40, r=40, t=50, b=40),
                )
                st.plotly_chart(fig_opt, use_container_width=True)

        # Harvest vs Yield Curve
        st.markdown("#### Harvest Fraction vs. Sustainable Yield Curve")
        h_vals, yields, msy_h, msy_val = optimizer.generate_uniform_yield_curve(
            x0=x0, num_points=40, sim_steps=50
        )
        fig_curve = go.Figure()
        fig_curve.add_trace(go.Scatter(
            x=h_vals * 100.0, y=yields,
            mode="lines", name="Sustainable Yield Curve",
            line=dict(color="#10B981", width=3)
        ))
        fig_curve.add_trace(go.Scatter(
            x=[msy_h * 100.0], y=[msy_val],
            mode="markers+text", name=f"MSY Peak ({msy_h*100:.1f}%, {msy_val:.1f})",
            marker=dict(size=14, color="#EF4444", symbol="diamond"),
            text=[f"MSY Point: {msy_h*100:.1f}%"], textposition="top center"
        ))
        fig_curve.update_layout(
            title="Uniform Harvest Fraction (h) vs. Equilibrium Yield",
            xaxis_title="Uniform Harvest Fraction (%)",
            yaxis_title="Annual Harvest Yield",
            template="plotly_dark",
            margin=dict(l=40, r=40, t=50, b=40),
        )
        st.plotly_chart(fig_curve, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 4: PHASE SPACE PORTRAIT
    # -------------------------------------------------------------------------
    with tabs[3]:
        st.subheader("Demographic Phase Space Portrait & Attractor Dynamics")

        if engine.n_classes >= 2:
            # Phase portrait of Juvenile (Class 1) vs Adult (Sum of Classes 2..N)
            juv_none = traj_none[:, 0]
            adult_none = np.sum(traj_none[:, 1:], axis=1)

            juv_sust = traj_sust[:, 0]
            adult_sust = np.sum(traj_sust[:, 1:], axis=1)

            fig_phase = go.Figure()
            fig_phase.add_trace(go.Scatter(
                x=juv_none, y=adult_none,
                mode="lines+markers", name="No Harvest Trajectory",
                line=dict(color="#38BDF8", width=2),
                marker=dict(size=4),
            ))
            fig_phase.add_trace(go.Scatter(
                x=juv_sust, y=adult_sust,
                mode="lines+markers", name="Sustainable Harvest (Attractor)",
                line=dict(color="#10B981", width=2.5),
                marker=dict(size=5),
            ))
            # Mark starting point
            fig_phase.add_trace(go.Scatter(
                x=[juv_none[0]], y=[adult_none[0]],
                mode="markers+text", name="Initial State (t=0)",
                marker=dict(size=12, color="#F59E0B", symbol="square"),
                text=["x₀"], textposition="top right"
            ))

            fig_phase.update_layout(
                title="Phase Portrait: Juvenile (Age 1) vs. Adult Reproductive Population (Age 2+)",
                xaxis_title="Juvenile Abundance (Class 1)",
                yaxis_title="Adult Abundance (Classes 2+)",
                template="plotly_dark",
                margin=dict(l=40, r=40, t=50, b=40),
            )
            st.plotly_chart(fig_phase, use_container_width=True)
        else:
            st.info("Phase space requires at least 2 age classes.")

    # -------------------------------------------------------------------------
    # TAB 5: MONTE CARLO RISK & PVA
    # -------------------------------------------------------------------------
    with tabs[4]:
        st.subheader("Monte Carlo Population Viability Analysis (PVA)")

        mc_col1, mc_col2 = st.columns([1, 2])

        with mc_col1:
            st.markdown("#### Stochastic Risk Settings")
            mc_reps = st.slider("Monte Carlo Iterations", min_value=100, max_value=1000, value=300, step=50)
            mc_fec_cv = st.slider("Fecundity Environmental CV", min_value=0.0, max_value=0.5, value=0.15, step=0.05)
            mc_surv_cv = st.slider("Survival Environmental CV", min_value=0.0, max_value=0.3, value=0.06, step=0.02)
            cat_prob = st.slider("Catastrophe Disaster Annual Probability", min_value=0.0, max_value=0.15, value=0.04, step=0.01)
            cat_impact = st.slider("Catastrophe Shock Severity", min_value=0.1, max_value=0.8, value=0.40, step=0.05)
            mc_harvest = st.slider("Simulated Harvest Rate during PVA", min_value=0.0, max_value=0.5, value=float(h_sust), step=0.02)

            run_mc = st.button("🚀 Run Monte Carlo Simulation", use_container_width=True)

        # Run or use cached simulation
        simulator = MonteCarloSimulator(engine, random_seed=42)
        mc_res = simulator.run_simulation(
            x0=x0,
            years=min(50, steps),
            num_iterations=mc_reps,
            fecundity_cv=mc_fec_cv,
            survival_cv=mc_surv_cv,
            catastrophe_prob=cat_prob,
            catastrophe_impact=cat_impact,
            harvest_fraction=mc_harvest,
        )

        with mc_col2:
            st.markdown(f"#### Extinction Probability over 50 Years: **{mc_res['extinction_risk']*100:.1f}%**")
            p = mc_res["percentiles"]
            yrs = mc_res["years"]

            fig_mc = go.Figure()
            # 5th to 95th envelope
            fig_mc.add_trace(go.Scatter(
                x=list(yrs) + list(yrs[::-1]),
                y=list(p["p95"]) + list(p["p5"][::-1]),
                fill="toself", fillcolor="rgba(56, 189, 248, 0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="90% Confidence Interval (5-95%)",
            ))
            # 25th to 75th envelope
            fig_mc.add_trace(go.Scatter(
                x=list(yrs) + list(yrs[::-1]),
                y=list(p["p75"]) + list(p["p25"][::-1]),
                fill="toself", fillcolor="rgba(56, 189, 248, 0.3)",
                line=dict(color="rgba(255,255,255,0)"),
                name="50% Confidence Interval (25-75%)",
            ))
            # Median
            fig_mc.add_trace(go.Scatter(
                x=yrs, y=p["median"],
                line=dict(color="#38BDF8", width=2.5),
                name="Median Trajectory",
            ))
            # Quasi-extinction threshold
            q_thresh = mc_res["quasi_extinction_threshold"]
            fig_mc.add_trace(go.Scatter(
                x=[0, yrs[-1]], y=[q_thresh, q_thresh],
                line=dict(color="#EF4444", width=2, dash="dash"),
                name=f"Quasi-Extinction Threshold ({q_thresh:.0f})",
            ))

            fig_mc.update_layout(
                title="Stochastic Population Trajectory Fan Chart",
                xaxis_title="Simulation Horizon (Years)",
                yaxis_title="Total Population",
                template="plotly_dark",
                margin=dict(l=40, r=40, t=50, b=40),
            )
            st.plotly_chart(fig_mc, use_container_width=True)

        # Sensitivity & Elasticity Table
        st.markdown("#### Caswell Sensitivity & Elasticity Ranking")
        sens_analyzer = SensitivityAnalyzer(engine)
        sens_df = sens_analyzer.get_vital_rates_sensitivity_dataframe()
        st.dataframe(sens_df, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 6: REPORTS & DATA EXPORT
    # -------------------------------------------------------------------------
    with tabs[5]:
        st.subheader("Enterprise Audit Logging & Automated Telemetry Export")

        exporter = ReportExporter(engine)
        col_exp1, col_exp2, col_exp3 = st.columns(3)

        # 1. PDF Report Download
        with col_exp1:
            st.markdown("##### 📄 Analytical PDF Report")
            st.caption("Publication-grade multi-page document with executive summary, tables, and charts.")
            if st.button("Generate Analytical PDF", use_container_width=True):
                with st.spinner("Compiling publication PDF report..."):
                    pdf_path = f"BioHarvest_{engine.species_name.replace(' ', '_')}_Report.pdf"
                    exporter.generate_pdf_report(
                        filepath=pdf_path,
                        initial_population=x0,
                        time_steps=steps,
                        msy_results=opt_res,
                        monte_carlo_results=mc_res,
                    )
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="⬇️ Download PDF Document",
                        data=pdf_bytes,
                        file_name=pdf_path,
                        mime="application/pdf",
                        use_container_width=True,
                    )

        # 2. CSV Trajectory Download
        with col_exp2:
            st.markdown("##### 📊 Trajectory CSV Stream")
            st.caption("Raw time-series projection across scenarios and demographic age cohorts.")
            csv_path = f"BioHarvest_{engine.species_name.replace(' ', '_')}_Trajectories.csv"
            trajectories_dict = {
                "No_Harvest": traj_none,
                "Sustainable_Uniform": traj_sust,
                "Over_Harvest": traj_over,
            }
            exporter.export_csv_trajectory(steps, trajectories_dict, csv_path)
            with open(csv_path, "rb") as f:
                csv_bytes = f.read()
            st.download_button(
                label="⬇️ Download CSV Telemetry",
                data=csv_bytes,
                file_name=csv_path,
                mime="text/csv",
                use_container_width=True,
            )

        # 3. JSON Telemetry Download
        with col_exp3:
            st.markdown("##### 🔧 JSON Telemetry Audit")
            st.caption("Complete model configuration, spectral invariants, and optimization state.")
            json_str = exporter.export_json_telemetry(
                msy_results=opt_res,
                monte_carlo_results=mc_res,
            )
            st.download_button(
                label="⬇️ Download JSON Telemetry",
                data=json_str,
                file_name=f"BioHarvest_{engine.species_name.replace(' ', '_')}_Telemetry.json",
                mime="application/json",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
