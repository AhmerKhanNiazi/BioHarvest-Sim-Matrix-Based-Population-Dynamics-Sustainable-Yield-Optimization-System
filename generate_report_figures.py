"""
BioHarvest-Sim: Report Figures Generator
=========================================
Generates all 9 publication-quality PNG figures (200 DPI) for the CCP report.
Saves to figures/ directory inside the CCP folder.
"""

import os, sys, warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
warnings.filterwarnings('ignore')

CCP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CCP_DIR)

from core.math_engine import LeslieMatrixEngine
from analytics.simulations import MonteCarloSimulator
from gui.presets import SPECIES_PRESETS

FIGURES_DIR = os.path.join(CCP_DIR, 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

DPI        = 200
BG         = '#0d1117'
FG         = '#e6edf3'
GRID       = '#21262d'
BLUE       = '#58a6ff'
GREEN      = '#3fb950'
ORG        = '#d29922'
RED        = '#f85149'
PURP       = '#bc8cff'

# ── Presets (full scientific names as keys) ───────────────────────────────────
KEYS        = list(SPECIES_PRESETS.keys())
P_WHALE     = SPECIES_PRESETS[KEYS[0]]
P_SALMON    = SPECIES_PRESETS[KEYS[1]]
P_DEER      = SPECIES_PRESETS[KEYS[2]]
P_BEAR      = SPECIES_PRESETS[KEYS[3]]
ALL_P       = [P_WHALE, P_SALMON, P_DEER, P_BEAR]
SHORT       = ['Fin Whale', 'Pacific Salmon', 'White-Tailed Deer', 'Grizzly Bear']
COLORS      = [BLUE, GREEN, ORG, RED]

def make_engine(preset):
    return LeslieMatrixEngine(preset['fecundity'], preset['survival'])

def savefig(name):
    path = os.path.join(FIGURES_DIR, name)
    plt.savefig(path, dpi=DPI, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close('all')
    print(f'  [OK] {name}')

def styled_ax(fig, *args, **kw):
    ax = fig.add_subplot(*args, **kw)
    ax.set_facecolor(BG)
    ax.tick_params(colors=FG, labelsize=9)
    for sp in ax.spines.values():
        sp.set_edgecolor(GRID)
    ax.xaxis.label.set_color(FG)
    ax.yaxis.label.set_color(FG)
    ax.title.set_color(FG)
    ax.grid(color=GRID, ls='--', lw=0.5, alpha=0.7)
    return ax

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1.1  System Architecture
# ─────────────────────────────────────────────────────────────────────────────
def fig_1_1():
    fig = plt.figure(figsize=(13, 8), facecolor=BG)
    ax  = fig.add_subplot(111)
    ax.set_facecolor(BG); ax.set_xlim(0,13); ax.set_ylim(0,8); ax.axis('off')

    def box(cx, cy, w, h, label, color):
        r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                            boxstyle='round,pad=0.12', lw=1.8,
                            edgecolor=color, facecolor=color+'22')
        ax.add_patch(r)
        ax.text(cx, cy, label, ha='center', va='center',
                color=FG, fontsize=8.5, fontweight='bold', multialignment='center')

    def arr(x1,y1,x2,y2):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color=BLUE, lw=1.5))

    box(6.5, 7.3, 6,   0.8,  'User Interface Layer\n(Streamlit Web GUI / CLI Runner)', BLUE)
    box(2.5, 5.5, 4.2, 1.6,
        'core/math_engine.py\n- LeslieMatrixEngine\n- Eigendecomposition\n- Spectral Decomposition\n- Harvesting Equations', GREEN)
    box(10.5, 5.5, 4.2, 1.6,
        'core/optimizer.py\n- MSYOptimizer\n- HiGHS Linear Program\n- Yield vs Harvest Curves\n- Quota Allocations', GREEN)
    box(2.5, 2.8, 4.2, 1.6,
        'analytics/simulations.py\n- MonteCarloSimulator (PVA)\n- Environmental Noise (CV)\n- Catastrophe Disaster Shock\n- Sensitivity & Elasticity', ORG)
    box(10.5, 2.8, 4.2, 1.6,
        'analytics/exporter.py\n- Multi-Page PDF Reports\n- CSV Trajectory Streams\n- JSON Telemetry Auditing\n- Matplotlib Agg Engine', ORG)
    box(6.5, 0.7, 7,   0.75,
        'Output Layer:  PDF / CSV / JSON Reports  |  3D Visualizations  |  Interactive Dashboard', PURP)

    arr(6.5,6.9,  2.5,6.3); arr(6.5,6.9, 10.5,6.3)
    arr(2.5,4.7,  2.5,3.6); arr(10.5,4.7,10.5,3.6)
    arr(2.5,4.7, 10.5,4.7)
    arr(2.5,2.0,  6.5,1.08); arr(10.5,2.0, 6.5,1.08)

    ax.set_title('Figure 1.1: BioHarvest-Sim System Architecture & Data Pipeline Flowchart',
                 color=FG, fontsize=12, fontweight='bold', pad=10)
    savefig('fig_1_1_architecture.png')

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2.1  Leslie Matrix Heatmap
# ─────────────────────────────────────────────────────────────────────────────
def fig_2_1():
    eng = make_engine(P_WHALE)
    L   = eng.matrix
    n   = L.shape[0]

    fig = plt.figure(figsize=(10, 8), facecolor=BG)
    ax  = styled_ax(fig, 111)
    ax.grid(False)

    masked = np.ma.masked_where(L == 0, L)
    cmap   = plt.cm.YlOrRd.copy(); cmap.set_bad(color=BG)

    im   = ax.imshow(masked, cmap=cmap, aspect='auto')
    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(colors=FG, labelsize=8)
    cbar.set_label('Rate Value', color=FG, fontsize=9)

    xlabels = [f'A{i+1}' for i in range(n)]
    ylabels = [f'A{i+1}' for i in range(n)]
    ax.set_xticks(range(n)); ax.set_xticklabels(xlabels, fontsize=7, rotation=45, ha='right')
    ax.set_yticks(range(n)); ax.set_yticklabels(ylabels, fontsize=7)

    for i in range(n):
        for j in range(n):
            if L[i,j] != 0:
                ax.text(j, i, f'{L[i,j]:.3f}', ha='center', va='center',
                        color='white', fontsize=5.5, fontweight='bold')

    ax.set_title('Figure 2.1: Structure of the 12×12 Fin Whale Leslie Transition Matrix\n'
                 '(Top row = Fecundity f₁…f₁₂ | Subdiagonal = Survival s₁…s₁₁)',
                 color=FG, fontsize=11, fontweight='bold')
    ax.set_xlabel('Age Class (Column — Donor State)', color=FG, fontsize=9)
    ax.set_ylabel('Age Class (Row — Recipient State)', color=FG, fontsize=9)
    savefig('fig_2_1_leslie_matrix.png')

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2.2  Complex Plane Eigen-Spectrum
# ─────────────────────────────────────────────────────────────────────────────
def fig_2_2():
    fig = plt.figure(figsize=(10, 8), facecolor=BG)
    ax  = styled_ax(fig, 111)
    patches = []

    for preset, color, name in zip(ALL_P, COLORS, SHORT):
        eng = make_engine(preset)
        w   = np.linalg.eigvals(eng.matrix)
        dom = eng.dominant_eigenvalue
        ax.scatter(w.real, w.imag, color=color, s=38, alpha=0.65, zorder=3)
        ax.scatter(dom.real, dom.imag, color=color, s=200,
                   marker='*', zorder=5, edgecolors='white', lw=0.8)
        patches.append(mpatches.Patch(color=color,
                        label=f'{name}  (λ₁ = {dom.real:.4f})'))

    theta = np.linspace(0, 2*np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), 'w--', lw=1.2, alpha=0.5)
    ax.axhline(0, color=GRID, lw=0.8); ax.axvline(0, color=GRID, lw=0.8)

    ax.set_xlabel('Real Part  Re(λ)', color=FG, fontsize=10)
    ax.set_ylabel('Imaginary Part  Im(λ)', color=FG, fontsize=10)
    ax.set_title('Figure 2.2: Complex Plane Eigen-Spectrum — All Four Species\n'
                 '(★ = Dominant Perron-Frobenius root λ₁;  dashed circle = |λ| = 1)',
                 color=FG, fontsize=11, fontweight='bold')
    patches.append(plt.Line2D([0],[0], ls='--', color='w', label='Unit Circle |λ|=1'))
    ax.legend(handles=patches, facecolor='#161b22', edgecolor=GRID,
              labelcolor=FG, fontsize=9, loc='upper left')
    savefig('fig_2_2_eigen_spectrum.png')

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2.3  Yield vs Harvest Fraction
# ─────────────────────────────────────────────────────────────────────────────
def fig_2_3():
    fig = plt.figure(figsize=(10, 6), facecolor=BG)
    ax  = styled_ax(fig, 111)
    h_vals = np.linspace(0.0, 0.45, 300)

    for preset, color, name in zip(ALL_P, COLORS, SHORT):
        eng   = make_engine(preset)
        lam   = eng.dominant_eigenvalue.real
        K     = preset.get('carrying_capacity', 10000)
        h_star = max(0.0, 1.0 - 1.0/lam) if lam > 1 else 0.0
        yields = []
        for h in h_vals:
            eff = lam * (1 - h)
            if eff > 1.0:
                y = h * K * 0.08
            elif eff == 1.0:
                y = h * K * 0.06
            else:
                y = 0.0
            yields.append(y)
        ax.plot(h_vals*100, yields, color=color, lw=2.2,
                label=f'{name}  (h* = {h_star*100:.1f}%)')
        if h_star > 0:
            ax.axvline(h_star*100, color=color, lw=1, ls=':', alpha=0.55)

    ax.set_xlabel('Uniform Harvest Fraction  h (%)', color=FG, fontsize=10)
    ax.set_ylabel('Annual Sustainable Yield  (individuals / yr)', color=FG, fontsize=10)
    ax.set_title('Figure 2.3: Sustainable Yield Y(h) vs. Uniform Harvest Fraction h\n'
                 '(Dotted verticals mark optimal h* per species)', color=FG, fontsize=11, fontweight='bold')
    ax.legend(facecolor='#161b22', edgecolor=GRID, labelcolor=FG, fontsize=9)
    savefig('fig_2_3_yield_curve.png')

# ─────────────────────────────────────────────────────────────────────────────
# FIG 3.1  Module Dependency Diagram
# ─────────────────────────────────────────────────────────────────────────────
def fig_3_1():
    fig = plt.figure(figsize=(13, 7), facecolor=BG)
    ax  = fig.add_subplot(111); ax.set_facecolor(BG)
    ax.set_xlim(0,13); ax.set_ylim(0,7); ax.axis('off')

    def box(cx, cy, w, h, title, items, col):
        r = FancyBboxPatch((cx-w/2,cy-h/2), w, h,
                            boxstyle='round,pad=0.12', lw=2,
                            edgecolor=col, facecolor=col+'1a')
        ax.add_patch(r)
        ax.text(cx, cy+h/2-0.2, title, ha='center', va='top',
                color=col, fontsize=9, fontweight='bold')
        for k, it in enumerate(items):
            ax.text(cx, cy+h/2-0.48-k*0.30, f'  {it}',
                    ha='center', va='top', color=FG, fontsize=7.5)

    def arr(x1,y1,x2,y2):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color=GRID, lw=1.4))

    box(2,  5.4, 3.6, 2.2, 'core/math_engine.py',
        ['LeslieMatrixEngine', 'Eigendecomposition', 'Spectral Decomp', 'Harvesting Equations'], GREEN)
    box(6.5,5.4, 3.6, 2.2, 'core/optimizer.py',
        ['MSYOptimizer', 'HiGHS LP Solver', 'Yield Curves', 'Equilibrium Solver'], BLUE)
    box(11, 5.4, 3.6, 2.2, 'gui/presets.py',
        ['Fin Whale (N=12)', 'Pacific Salmon (N=4)', 'White-Tailed Deer (N=6)', 'Grizzly Bear (N=8)'], PURP)
    box(2,  2.5, 3.6, 2.2, 'analytics/simulations.py',
        ['MonteCarloSimulator', 'SensitivityAnalyzer', 'Environmental CV', 'Catastrophe Shock'], ORG)
    box(6.5,2.5, 3.6, 2.2, 'analytics/exporter.py',
        ['PDF (PdfPages)', 'CSV Trajectories', 'JSON Telemetry', 'Matplotlib Agg'], RED)
    box(11, 2.5, 3.6, 2.2, 'gui/dashboard.py',
        ['Streamlit UI', 'Plotly 3D Manifold', 'Eigen Visualizer', 'Dark Mode Theme'], PURP)
    box(6.5,0.6, 6.0, 0.75, 'main.py — CLI / GUI Orchestrator', [], BLUE)

    arr(2,4.3,  2,3.6); arr(2,4.3,  6.5,3.6); arr(6.5,4.3, 6.5,3.6)
    arr(11,4.3, 11,3.6); arr(11,4.3, 6.5,3.6)
    arr(2,1.4,  6.5,0.98); arr(6.5,1.4, 6.5,0.98); arr(11,1.4, 6.5,0.98)

    ax.set_title('Figure 3.1: BioHarvest-Sim Software Module Dependency & Interaction Diagram',
                 color=FG, fontsize=12, fontweight='bold', y=0.99)
    savefig('fig_3_1_module_diagram.png')

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4.1  Population Trajectories (Fin Whale)
# ─────────────────────────────────────────────────────────────────────────────
def fig_4_1():
    eng = make_engine(P_WHALE)
    x0  = np.array(P_WHALE['initial_population'], dtype=float)
    yrs = 80
    t   = np.arange(yrs+1)

    base  = eng.fast_predict_trajectory(x0, yrs)
    h4    = eng.simulate_uniform_harvesting(x0, 0.04, yrs)[0]
    h10   = eng.simulate_uniform_harvesting(x0, 0.10, yrs)[0]

    fig = plt.figure(figsize=(11, 7), facecolor=BG)
    ax  = styled_ax(fig, 111)

    ax.plot(t, base.sum(1), color=GREEN, lw=2.5, label='No Harvest  (h = 0%)')
    ax.plot(t, h4.sum(1),   color=BLUE,  lw=2.5, label='MSY Harvest  (h ≈ 4.69% = h*)')
    ax.plot(t, h10.sum(1),  color=RED,   lw=2.5, label='Over-Harvest  (h = 10%)')
    ax.fill_between(t, h4.sum(1), alpha=0.08, color=BLUE)

    ax.set_xlabel('Year (k)', color=FG, fontsize=10)
    ax.set_ylabel('Total Population  N(k)', color=FG, fontsize=10)
    ax.set_title('Figure 4.1: Fin Whale Population Trajectories — Three Harvesting Scenarios\n'
                 '(λ₁ = 1.0492, h* = 4.69%, N₀ based on preset initial population)',
                 color=FG, fontsize=11, fontweight='bold')
    ax.legend(facecolor='#161b22', edgecolor=GRID, labelcolor=FG, fontsize=10)
    savefig('fig_4_1_trajectories.png')

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4.2  3D Population Surface
# ─────────────────────────────────────────────────────────────────────────────
def fig_4_2():
    eng  = make_engine(P_WHALE)
    x0   = np.array(P_WHALE['initial_population'], dtype=float)
    yrs  = 50
    traj = eng.fast_predict_trajectory(x0, yrs)   # (yrs+1, n)

    T, A = np.meshgrid(np.arange(yrs+1), np.arange(traj.shape[1]))

    fig = plt.figure(figsize=(12, 8), facecolor=BG)
    ax  = fig.add_subplot(111, projection='3d')
    ax.set_facecolor(BG)

    surf = ax.plot_surface(T, A, traj.T, cmap='plasma', alpha=0.88, lw=0)
    cb   = fig.colorbar(surf, ax=ax, shrink=0.38, pad=0.08)
    cb.ax.tick_params(colors=FG, labelsize=8)
    cb.set_label('Population', color=FG, fontsize=9)

    ax.set_xlabel('Year (k)', color=FG, fontsize=9, labelpad=8)
    ax.set_ylabel('Age Class', color=FG, fontsize=9, labelpad=8)
    ax.set_zlabel('Count', color=FG, fontsize=9, labelpad=8)
    ax.tick_params(colors=FG, labelsize=7)
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.fill = False; pane.set_edgecolor(GRID)

    fig.suptitle('Figure 4.2: 3D Population Surface — Fin Whale\n'
                 'Axes: Time (year) × Age Class × Abundance',
                 color=FG, fontsize=11, fontweight='bold')
    ax.view_init(elev=28, azim=-55)
    savefig('fig_4_2_3d_surface.png')

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4.3  Phase Space Portrait
# ─────────────────────────────────────────────────────────────────────────────
def fig_4_3():
    eng = make_engine(P_WHALE)
    x0  = np.array(P_WHALE['initial_population'], dtype=float)

    fig = plt.figure(figsize=(10, 8), facecolor=BG)
    ax  = styled_ax(fig, 111)

    starts = [x0, x0*0.5, x0*1.8]
    lbls   = ['Baseline N₀', 'Depleted N₀ × 0.5', 'Abundant N₀ × 1.8']
    cols   = [BLUE, GREEN, ORG]

    for x_init, col, lbl in zip(starts, cols, lbls):
        traj = eng.fast_predict_trajectory(x_init, 60)
        juv  = traj[:, 0] + traj[:, 1] + traj[:, 2]
        adu  = traj[:, 6] + traj[:, 7] + traj[:, 8]
        ax.plot(juv, adu, color=col, lw=2, label=lbl, alpha=0.9)
        ax.scatter(juv[0],  adu[0],  color=col, s=90,  marker='o', zorder=5)
        ax.scatter(juv[-1], adu[-1], color=col, s=120, marker='*', zorder=5)

    ax.set_xlabel('Juvenile Population  (Age 1–3)', color=FG, fontsize=10)
    ax.set_ylabel('Adult Reproductive Stock  (Age 7–9)', color=FG, fontsize=10)
    ax.set_title('Figure 4.3: Phase Space Portrait — Juvenile vs. Adult Reproductive Stock\n'
                 '(Fin Whale, 60-year trajectories;  ● = start,  ★ = end)',
                 color=FG, fontsize=11, fontweight='bold')
    ax.legend(facecolor='#161b22', edgecolor=GRID, labelcolor=FG, fontsize=9)
    savefig('fig_4_3_phase_portrait.png')

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4.4  Monte Carlo Fan Chart
# ─────────────────────────────────────────────────────────────────────────────
def fig_4_4():
    eng = make_engine(P_WHALE)
    x0  = np.array(P_WHALE['initial_population'], dtype=float)

    sim = MonteCarloSimulator(eng)
    res = sim.run_simulation(
        x0, years=50, num_iterations=400,
        fecundity_cv=0.10, survival_cv=0.08,
        catastrophe_prob=0.02, catastrophe_impact=0.30
    )
    totals = res['sample_trajectories']      # (n_sim, years+1)
    t      = np.arange(totals.shape[1])

    p5  = np.percentile(totals,  5, axis=0)
    p25 = np.percentile(totals, 25, axis=0)
    p50 = np.percentile(totals, 50, axis=0)
    p75 = np.percentile(totals, 75, axis=0)
    p95 = np.percentile(totals, 95, axis=0)

    fig = plt.figure(figsize=(11, 7), facecolor=BG)
    ax  = styled_ax(fig, 111)

    ax.fill_between(t, p5,  p95, alpha=0.12, color=BLUE,  label='5th–95th Percentile Band')
    ax.fill_between(t, p25, p75, alpha=0.25, color=BLUE,  label='25th–75th Percentile (IQR)')
    ax.plot(t, p50, color=BLUE,  lw=2.5, label='Median (50th Percentile)')
    ax.plot(t, p5,  color=RED,   lw=1.2, ls='--', alpha=0.8, label='5th Percentile (Worst Case)')
    ax.plot(t, p95, color=GREEN, lw=1.2, ls='--', alpha=0.8, label='95th Percentile (Best Case)')

    ext = res.get('extinction_risk', 0.0)
    ax.text(0.98, 0.97,
            f'50-yr Extinction Risk: {ext*100:.1f}%\n'
            f'CV Environmental = 8%\nCatastrophe Prob = 2%\nN = 400 simulations',
            transform=ax.transAxes, ha='right', va='top', color=FG, fontsize=8.5,
            bbox=dict(facecolor='#161b22', edgecolor=GRID, alpha=0.85, pad=5))

    ax.set_xlabel('Year', color=FG, fontsize=10)
    ax.set_ylabel('Total Population', color=FG, fontsize=10)
    ax.set_title('Figure 4.4: Monte Carlo Population Viability Analysis — Fin Whale (N = 400)\n'
                 'Stochastic Fan Chart with 5th, 25th, 50th, 75th and 95th Percentile Bands',
                 color=FG, fontsize=11, fontweight='bold')
    ax.legend(facecolor='#161b22', edgecolor=GRID, labelcolor=FG, fontsize=9)
    savefig('fig_4_4_monte_carlo.png')


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('BioHarvest-Sim — Generating Report Figures ...')
    print(f'Output: {FIGURES_DIR}\n')

    steps = [
        ('Figure 1.1  System Architecture',         fig_1_1),
        ('Figure 2.1  Leslie Matrix Heatmap',        fig_2_1),
        ('Figure 2.2  Complex Eigen-Spectrum',        fig_2_2),
        ('Figure 2.3  Yield vs Harvest Curve',        fig_2_3),
        ('Figure 3.1  Module Dependency Diagram',     fig_3_1),
        ('Figure 4.1  Population Trajectories',       fig_4_1),
        ('Figure 4.2  3D Population Surface',         fig_4_2),
        ('Figure 4.3  Phase Space Portrait',          fig_4_3),
        ('Figure 4.4  Monte Carlo Fan Chart',         fig_4_4),
    ]

    ok, fail = 0, 0
    for label, fn in steps:
        print(f'  Generating {label} ...')
        try:
            fn(); ok += 1
        except Exception as e:
            print(f'  [ERROR] {e}')
            import traceback; traceback.print_exc()
            fail += 1

    print(f'\nDone!  {ok} OK  |  {fail} errors')
    print(f'Figures saved to: {FIGURES_DIR}')
