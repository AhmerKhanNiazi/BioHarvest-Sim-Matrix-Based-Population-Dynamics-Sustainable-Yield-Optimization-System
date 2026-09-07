# BioHarvest-Sim: Matrix-Based Population Dynamics & Sustainable Yield Optimization System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ISO/IEC/IEEE 12207](https://img.shields.io/badge/Standard-ISO%2FIEC%2FIEEE%2012207-orange.svg)]()
[![Code Style: PEP-8](https://img.shields.io/badge/code%20style-PEP--8-black.svg)]()

> **University-Level Complex Computing Project (CCP)**  
> **Core Domain:** Advanced Linear Algebra (Leslie Matrices, Perron-Frobenius Theorem, Spectral Decomposition) & Mathematical Optimization (Linear Programming via HiGHS).

---

## Executive Summary & System Overview

**BioHarvest-Sim** is an enterprise-grade, high-performance computational environment for modeling age-structured biological populations, computing asymptotic demographic stability via eigendecomposition, determining Maximum Sustainable Yield (MSY) through linear programming, and conducting stochastic Population Viability Analysis (PVA).

The platform bridges **pure linear algebraic theory** with **practical ecological resource management**, adhering strictly to Agile Methodologies and International Software Engineering Standards (ISO/IEC/IEEE 12207 & 27001).

---

## System Architecture

```
                                  +---------------------------------------+
                                  |         User Interface Layer          |
                                  |   (Streamlit Web GUI / CLI Runner)    |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                        +-----------------------------+-----------------------------+
                        |                                                           |
                        v                                                           v
        +-------------------------------+                           +-------------------------------+
        |     core/math_engine.py       |                           |      core/optimizer.py        |
        |  - LeslieMatrixEngine         |                           |  - MSYOptimizer               |
        |  - Eigendecomposition         |                           |  - HiGHS Linear Program       |
        |  - Spectral Decomposition     |                           |  - Yield vs. Harvest Curves   |
        |  - Harvesting Equations       |                           |  - Quota Allocations          |
        +---------------+---------------+                           +---------------+---------------+
                        |                                                           |
                        +-----------------------------+-----------------------------+
                                                      |
                                                      v
                        +-----------------------------+-----------------------------+
                        |                                                           |
                        v                                                           v
        +-------------------------------+                           +-------------------------------+
        |   analytics/simulations.py    |                           |     analytics/exporter.py     |
        |  - MonteCarloSimulator (PVA)  |                           |  - Multi-Page PDF Reports     |
        |  - Environmental Noise (CV)   |                           |  - CSV Trajectory Streams     |
        |  - Catastrophe Disaster Shock |                           |  - JSON Telemetry Auditing    |
        |  - Sensitivity & Elasticity   |                           |  - Matplotlib Agg Engine      |
        +-------------------------------+                           +-------------------------------+
```

### Mermaid.js Architectural Workflow

```mermaid
graph TD
    A[Demographic Parameters: f_i, s_i] --> B[LeslieMatrixEngine]
    B --> C[Characteristic Polynomial & det(L - λI) = 0]
    C --> D[Perron-Frobenius Dominant Eigendecomposition]
    D --> E[Intrinsic Growth Rate r = ln λ1]
    D --> F[Stable Age Distribution w1]
    D --> G[Fisher Reproductive Value u1]
    D --> H[Spectral Decomposition L = P D P^-1]
    
    H --> I[Fast Trajectory Acceleration L^k x0]
    B --> J[Caswell Perturbation: Sensitivity & Elasticity]
    
    B --> K[MSY Linear Programming Optimizer]
    K --> L[Simplex/HiGHS: Maximize c^T h subject to (I-L)x + Lh = 0]
    
    B --> M[Monte Carlo Stochastic Engine]
    M --> N[Environmental Stochasticity & Catastrophe Shocks]
    N --> O[50-Year Extinction Risk & PVA Confidence Envelopes]
    
    I & L & O --> P[Interactive Streamlit & Plotly 3D Visualizer]
    I & L & O --> Q[Automated PDF / CSV / JSON Reporting Engine]
```

---

## Formal Mathematical Foundations & Proofs

### 1. The Discrete-Time Leslie Population Matrix

Let a biological population be partitioned into $n$ chronological age classes:
$$\mathbf{x}_k = \begin{bmatrix} x_{1,k} \\ x_{2,k} \\ \vdots \\ x_{n,k} \end{bmatrix}$$
where $x_{i,k}$ denotes the number of individuals in age class $i$ at time step $k$.

The transition from state $\mathbf{x}_k$ to $\mathbf{x}_{k+1}$ is governed by the $n \times n$ **Leslie Matrix** $L$:
$$L = \begin{bmatrix}
f_1 & f_2 & f_3 & \dots & f_{n-1} & f_n \\
s_1 & 0 & 0 & \dots & 0 & 0 \\
0 & s_2 & 0 & \dots & 0 & 0 \\
\vdots & \vdots & \ddots & \dots & \vdots & \vdots \\
0 & 0 & \dots & s_{n-1} & 0 & 0
\end{bmatrix}$$
where:
- $f_i \ge 0$: Age-specific fecundity rate (average number of offspring born to an individual in age class $i$ that survive to the next census).
- $s_i \in (0, 1]$: Survival probability of an individual in age class $i$ transitioning into age class $i+1$.

The discrete system equation is:
$$\mathbf{x}_{k+1} = L \mathbf{x}_k$$

---

### 2. The Perron-Frobenius Theorem & Asymptotic Stability

#### Theorem (Perron-Frobenius for Non-Negative Matrices)
Let $L \ge 0$ be an irreducible, non-negative matrix.
1. The spectral radius $\rho(L) = \max_j |\lambda_j|$ is an eigenvalue of $L$, denoted $\lambda_1$.
2. $\lambda_1$ is real and strictly positive: $\lambda_1 > 0$.
3. Associated with $\lambda_1$ is a strictly positive right eigenvector $\mathbf{v}_1 > \mathbf{0}$ such that:
   $$L \mathbf{v}_1 = \lambda_1 \mathbf{v}_1$$
4. $\lambda_1$ is a simple root of the characteristic polynomial $p(\lambda) = \det(\lambda I - L) = 0$.
5. If $L$ is **primitive** (i.e. there exists $m > 0$ such that $L^m > \mathbf{0}$, which holds whenever $\gcd\{i : f_i > 0\} = 1$), then for all other eigenvalues $\lambda_j \ne \lambda_1$:
   $$|\lambda_j| < \lambda_1$$

#### Demographic Invariants:
- **Intrinsic Growth Rate ($r$):**
  $$r = \ln(\lambda_1)$$
  - $\lambda_1 > 1 \implies r > 0$: Exponential population expansion.
  - $\lambda_1 = 1 \implies r = 0$: Stationary population equilibrium.
  - $\lambda_1 < 1 \implies r < 0$: Exponential population extinction.
- **Stable Age Distribution ($\mathbf{w}$):**
  $$\mathbf{w} = \frac{\mathbf{v}_1}{\sum_{i=1}^n v_{1,i}}, \quad \lim_{k \to \infty} \frac{\mathbf{x}_k}{\sum_{i=1}^n x_{i,k}} = \mathbf{w}$$
- **Fisher's Reproductive Value ($\mathbf{u}$):**
  The dominant left eigenvector:
  $$\mathbf{u}^T L = \lambda_1 \mathbf{u}^T$$
  Normalized such that $u_1 = 1.0$, measuring the relative expected future reproductive contribution of each age cohort.

---

### 3. Spectral Decomposition & Fast $k$-Step Trajectory

If $L$ is diagonalizable, there exists an invertible modal matrix $P = [\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_n]$ and a diagonal spectral matrix $D = \text{diag}(\lambda_1, \lambda_2, \dots, \lambda_n)$ such that:
$$L = P D P^{-1}$$

Hence, the population at arbitrary future step $k$ satisfies:
$$\mathbf{x}_k = L^k \mathbf{x}_0 = (P D P^{-1})^k \mathbf{x}_0 = P D^k P^{-1} \mathbf{x}_0$$

Let $\mathbf{c} = P^{-1} \mathbf{x}_0 = [c_1, c_2, \dots, c_n]^T$. Then:
$$\mathbf{x}_k = \sum_{j=1}^n c_j \lambda_j^k \mathbf{v}_j = c_1 \lambda_1^k \mathbf{v}_1 + \sum_{j=2}^n c_j \lambda_j^k \mathbf{v}_j$$

Dividing by $\lambda_1^k$:
$$\frac{\mathbf{x}_k}{\lambda_1^k} = c_1 \mathbf{v}_1 + \sum_{j=2}^n c_j \left(\frac{\lambda_j}{\lambda_1}\right)^k \mathbf{v}_j$$

Since $|\lambda_j / \lambda_1| < 1$ for primitive $L$, the summation vanishes exponentially as $k \to \infty$. The convergence rate is governed by the **Damping Ratio**:
$$\rho = \frac{\lambda_1}{|\lambda_2|}$$

---

### 4. Euler-Lotka Equation & Net Reproductive Rate ($R_0$)

By expanding $\det(\lambda I - L) = 0$ along the first row:
$$\lambda^n - f_1 \lambda^{n-1} - f_2 s_1 \lambda^{n-2} - f_3 s_1 s_2 \lambda^{n-3} - \dots - f_n s_1 s_2 \dots s_{n-1} = 0$$

Dividing by $\lambda^n$ yields the discrete **Euler-Lotka Characteristic Equation**:
$$\sum_{i=1}^n l_i f_i \lambda^{-i} = 1$$
where $l_1 = 1$ and $l_i = \prod_{j=1}^{i-1} s_j$ is survivorship to age class $i$.

Evaluating at $\lambda = 1$ yields the **Net Reproductive Rate ($R_0$)**:
$$R_0 = \sum_{i=1}^n l_i f_i$$
- $R_0 > 1 \iff \lambda_1 > 1$
- $R_0 = 1 \iff \lambda_1 = 1$
- $R_0 < 1 \iff \lambda_1 < 1$

---

### 5. Harvesting Theory & Maximum Sustainable Yield (MSY)

#### Uniform Harvesting Strategy
If a uniform fraction $h \in [0, 1)$ of all age classes is harvested immediately after reproduction:
$$\mathbf{x}_{k+1} = (1 - h) L \mathbf{x}_k$$
The effective projection matrix is $\tilde{L} = (1 - h) L$. Its dominant eigenvalue is:
$$\tilde{\lambda}_1 = (1 - h) \lambda_1$$
To maintain a stationary population ($\tilde{\lambda}_1 = 1$):
$$(1 - h) \lambda_1 = 1 \implies h^* = 1 - \frac{1}{\lambda_1}$$
This sustainable yield fraction $h^*$ exists if and only if $\lambda_1 > 1$.

#### Maximum Sustainable Yield (MSY) Linear Program
Let $\mathbf{x}^* \ge \mathbf{0}$ be the equilibrium standing stock and $\mathbf{h}^* \ge \mathbf{0}$ be the sustainable harvest quota vector.
Under post-reproduction harvest:
$$\mathbf{x}^* = L \mathbf{x}^* - \mathbf{h}^* \iff (L - I) \mathbf{x}^* - \mathbf{h}^* = \mathbf{0}$$

We formulate the economic/biomass maximization as a **Linear Program**:
$$\max_{\mathbf{x}^*, \mathbf{h}^*} \mathbf{c}^T \mathbf{h}^*$$
subject to:
$$\begin{aligned}
(L - I) \mathbf{x}^* - \mathbf{h}^* &= \mathbf{0} \quad &&\text{(Demographic Equilibrium)} \\
\mathbf{h}^* &\le \alpha \odot \mathbf{x}^* \quad &&\text{(Harvest Bounds / Stage Protections)} \\
\sum_{i=1}^n x_i^* &\le K \quad &&\text{(Carrying Capacity)} \\
\mathbf{x}^* \ge \mathbf{0}, \quad \mathbf{h}^* &\ge \mathbf{0} \quad &&\text{(Physical Non-Negativity)}
\end{aligned}$$

Solved using modern dual-simplex / interior-point solvers via `scipy.optimize.linprog(method='highs')`.

---

### 6. Caswell Perturbation Theory: Sensitivity & Elasticity

- **Sensitivity Matrix ($S$):**
  $$S_{ij} = \frac{\partial \lambda_1}{\partial L_{ij}} = \frac{u_i v_j}{\mathbf{u}^T \mathbf{v}}$$
- **Elasticity Matrix ($E$):**
  $$E_{ij} = \frac{L_{ij}}{\lambda_1} \frac{\partial \lambda_1}{\partial L_{ij}} = \frac{L_{ij}}{\lambda_1} S_{ij}$$
- **Euler Homogeneity Property:**
  $$\sum_{i=1}^n \sum_{j=1}^n E_{ij} = 1.000$$

---

## Installation & Quick-Start

### Prerequisites
- Python 3.10, 3.11, or 3.12
- `git`

### 1. Clone & Setup Environment
```bash
git clone https://github.com/your-org/BioHarvest-Sim.git
cd BioHarvest-Sim
python -m venv .venv

# On Windows
.venv\Scripts\activate
# On Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run Automated Verification Suite
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 3. Launch Interactive Streamlit Dashboard
```bash
streamlit run gui/dashboard.py
# Or using the orchestrator:
python main.py --gui
```

### 4. Run CLI Pipeline & Generate Reports
```bash
# Run all presets and generate PDF/CSV/JSON artifacts:
python main.py

# Run for a specific species:
python main.py --species "Fin Whale"
```

---

## Directory Structure

```
BioHarvest-Sim/
├── core/
│   ├── __init__.py
│   ├── math_engine.py       # LeslieMatrixEngine, Spectral Analysis, Diagonalization
│   └── optimizer.py         # MSY Linear Programming (scipy.optimize.linprog HiGHS)
├── analytics/
│   ├── __init__.py
│   ├── simulations.py       # MonteCarloSimulator (PVA), SensitivityAnalyzer
│   └── exporter.py          # PDF Report (PdfPages), CSV Trajectories, JSON Telemetry
├── gui/
│   ├── __init__.py
│   ├── dashboard.py         # Streamlit Dark-Mode Dashboard with Plotly Visuals
│   └── presets.py           # Ecological Life Tables (Whale, Salmon, Deer, Bear)
├── tests/
│   ├── __init__.py
│   └── test_math.py         # Comprehensive unittest suite (17 test cases)
├── main.py                  # Unified CLI / GUI Launch Orchestrator
├── requirements.txt         # Project Dependencies
├── README.md                # Comprehensive Architecture & Mathematical Proofs
└── AGILE_PROJECT_DOCS.md    # Agile Epics, Gherkin User Stories & Sprint Backlogs
```

---

## Standards & Compliance

- **ISO/IEC/IEEE 12207:** Systems and software engineering — Software life cycle processes.
- **ISO/IEC/IEEE 27001:** Information security and data integrity management.
- **PEP-8 & Type Annotations:** 100% compliant with static type hints (`typing`).
