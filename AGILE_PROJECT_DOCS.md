# BioHarvest-Sim: Agile Project Documentation & Sprint Artifacts

**Standard:** ISO/IEC/IEEE 12207 (Software Life Cycle) & ISO/IEC 27001 (Information Security)  
**Project Methodology:** Agile Scrum Framework (4 Sprints, 2-Week Cadence)  
**Velocity Target:** 35 Story Points / Sprint  

---

## 1. Agile Framework & Scrum Governance

### Definition of Done (DoD)
A User Story is marked as **Done** only when:
1. **Mathematical Accuracy:** Formulas are verified against analytical proofs or peer-reviewed literature.
2. **Code Quality:** PEP-8 compliant, fully typed (`typing.Union`, `Optional`, `Tuple`, etc.), docstrings with NumPy/SciPy conventions.
3. **Test Coverage:** Automated unit tests written and passing in `tests/test_math.py` with 100% pass rate.
4. **Security & Validation:** No uncaught runtime exceptions; boundary constraints validated ($f_i \ge 0, 0 \le s_i \le 1$).
5. **Continuous Integration:** Executable via `main.py` and `streamlit run gui/dashboard.py`.

---

## 2. Sprint Backlogs & Velocity Metrics

| Sprint | Focus Area | Planned Points | Completed Points | Status |
|---|---|:---:|:---:|:---:|
| **Sprint 1** | Mathematical Core Engine & MSY Linear Programming | 34 | 34 | **COMPLETED** |
| **Sprint 2** | Interactive Desktop GUI Engine (Streamlit & Presets) | 32 | 32 | **COMPLETED** |
| **Sprint 3** | Dynamic Plotly 3D Surface & Spectral Visualizations | 36 | 36 | **COMPLETED** |
| **Sprint 4** | Monte Carlo PVA, PDF Reporting & Telemetry Exporter | 38 | 38 | **COMPLETED** |
| **Total** | Full Enterprise CCP Delivery | **140** | **140** | **100% DONE** |

### Sprint Burn-Down Table

```
Sprint Day | Planned Remaining (pts) | Actual Remaining (pts) | Notes
-----------+-------------------------+------------------------+---------------------------------------
Day 1      | 140                     | 140                    | Project kick-off & math modeling
Day 3      | 115                     | 112                    | Sprint 1 math core completed early
Day 5      | 90                      | 88                     | MSY HiGHS Linear Program verified
Day 7      | 65                      | 60                     | Streamlit GUI & real-world presets
Day 9      | 40                      | 35                     | Plotly 3D surface & complex plane
Day 11     | 20                      | 15                     | Monte Carlo PVA & Catastrophe shock
Day 14     | 0                       | 0                      | Multi-page PDF report & 17 unit tests
```

---

## 3. Epics & User Stories (Gherkin Syntax: Given-When-Then)

### EPIC 1: Mathematical Core Engine (Sprint 1)

#### User Story 1.1: Leslie Matrix Construction & Validation
> **As an** Applied Ecologist,  
> **I want to** instantiate an $N \times N$ Leslie matrix from age-class fecundities and survival probabilities,  
> **So that** I can accurately represent age-structured population transitions.

```gherkin
Scenario: Constructing a valid 3-age class Leslie Matrix
  Given a fecundity vector [0.0, 1.2, 1.8]
  And a survival probability vector [0.6, 0.5]
  When the LeslieMatrixEngine is initialized
  Then the resulting matrix dimensions must be 3x3
  And the first row must equal [0.0, 1.2, 1.8]
  And the subdiagonal entries must equal [0.6, 0.5]
  And all other entries must be 0.0

Scenario: Rejecting invalid biological survival rates
  Given a survival vector containing 1.25
  When the LeslieMatrixEngine is initialized
  Then a ValueError must be raised stating survival cannot exceed 1.0
```

#### User Story 1.2: Perron-Frobenius Dominant Eigendecomposition
> **As a** Quantitative Biologist,  
> **I want to** extract the dominant eigenvalue $\lambda_1$ and right eigenvector $\mathbf{v}_1$,  
> **So that** I can ascertain the long-term intrinsic growth rate and asymptotic stable age distribution.

```gherkin
Scenario: Identifying the dominant spectral pair
  Given an irreducible non-negative Leslie matrix L
  When spectral decomposition is performed
  Then the dominant eigenvalue lambda_1 must be real, strictly positive, and equal the spectral radius
  And the associated eigenvector v_1 must be strictly positive
  And the normalized stable age distribution w must sum to exactly 1.0
```

#### User Story 1.3: Maximum Sustainable Yield (MSY) Linear Program
> **As a** Wildlife Resource Manager,  
> **I want to** solve for the optimal stage-specific harvest vector $\mathbf{h}^*$ using linear programming,  
> **So that** harvest yield is maximized without endangering population sustainability.

```gherkin
Scenario: Optimizing harvest quota subject to demographic equilibrium
  Given a Leslie matrix L with lambda_1 > 1.0
  And a carrying capacity limit K = 1000
  When the MSY Linear Program is solved via the HiGHS solver
  Then the equilibrium condition (L - I)x* - h* = 0 must hold within 1e-4 tolerance
  And the total standing stock sum(x*) must not exceed K
  And optimal harvest h* must be non-negative and positive in surplus stages
```

---

### EPIC 2: Interactive GUI & Ecological Presets (Sprint 2)

#### User Story 2.1: Real-World Species Presets
> **As an** Academic Student or Researcher,  
> **I want to** load pre-configured parameters for Whales, Salmon, Deer, and Grizzly Bears,  
> **So that** I can explore realistic demographic dynamics without entering tables manually.

```gherkin
Scenario: Loading the Fin Whale preset
  Given the species preset "Fin Whale (Balaenoptera physalus)" is selected
  When parameters are inspected
  Then the model must load 12 age classes
  And sexual maturity must occur at age 5-6 (fecundity = 0 for ages 0-4)
  And adult survival rates must be >= 0.90
```

#### User Story 2.2: Real-Time Parameter Sliders & Scenarios
> **As an** Environmental Analyst,  
> **I want to** adjust vital rates via interactive sliders,  
> **So that** I can immediately assess the impact of environmental perturbations on $\lambda_1$.

```gherkin
Scenario: Comparing No-Harvest vs Over-Harvesting
  Given an initial population vector x_0
  When the simulation runs for 40 years across 3 scenarios
  Then the sustainable uniform harvest trajectory must converge to a constant stock
  And the over-harvesting trajectory must decline asymptotically toward 0
```

---

### EPIC 3: Dynamic Data Visualization Engine (Sprint 3)

#### User Story 3.1: 3D Population Surface Plot
> **As a** Scientific Presenter,  
> **I want to** view a 3D manifold plot of Time vs Age Class vs Population Count,  
> **So that** cohort propagation and demographic waves are intuitively comprehensible.

```gherkin
Scenario: Rendering Plotly 3D Surface
  Given a multi-cohort population trajectory over T time steps
  When the 3D surface visualizer renders the data
  Then the X-axis must represent time horizon [0, T]
  And the Y-axis must represent discrete age classes [1, N]
  And the Z-axis must represent the non-negative abundance counts
```

#### User Story 3.2: Complex Plane Eigen-Spectrum Visualizer
> **As a** Linear Algebra Student,  
> **I want to** visualize all eigenvalues relative to the complex unit circle $|\lambda| = 1$,  
> **So that** I can observe oscillatory modes and stability boundaries.

```gherkin
Scenario: Visualizing stability on the complex plane
  Given a Leslie matrix with complex conjugate subdominant eigenvalues
  When the spectrum is plotted
  Then a red dashed unit circle (|lambda| = 1) must be displayed
  And all eigenvalues must be plotted as coordinates (Re, Im)
  And the dominant eigenvalue lambda_1 must be highlighted with a distinctive marker
```

---

### EPIC 4: Enterprise Logging, Robustness & Exporters (Sprint 4)

#### User Story 4.1: Monte Carlo Population Viability Analysis (PVA)
> **As a** Conservation Biologist,  
> **I want to** simulate environmental stochasticity and disaster shocks over 50 years,  
> **So that** I can estimate the probability of functional quasi-extinction.

```gherkin
Scenario: Simulating 500 stochastic paths with catastrophe shocks
  Given a base population with environmental variance CV = 0.15
  And a catastrophe disaster probability of 4% per annum
  When the Monte Carlo simulator executes 500 iterations
  Then the 5th, 25th, 50th, 75th, and 95th percentiles must be ordered monotonically
  And an extinction probability within [0.0, 1.0] must be computed
```

#### User Story 4.2: Publication-Grade PDF & Telemetry Export
> **As a** University Evaluator,  
> **I want to** export simulation results to a multi-page PDF report and CSV/JSON telemetry,  
> **So that** audit trails and experimental records can be archived and reviewed offline.

```gherkin
Scenario: Exporting analytical artifacts
  Given completed simulation, MSY, and Monte Carlo runs
  When the ReportExporter compiles outputs
  Then a multi-page PDF file with executive summaries, tables, and graphs must be written
  And a structured JSON file containing model invariants must be serialized
  And a CSV file containing time-step cohort population counts must be created
```

---

## 4. Risk Assessment & Mitigation Matrix

| Risk ID | Description | Severity | Likelihood | Mitigation Strategy |
|:---:|---|:---:|:---:|---|
| **RSK-01** | Non-primitive Leslie matrix with equal modulus eigenvalues (e.g., pure semelparous life cycles like Pacific Salmon). | High | Medium | Implemented robust root selection favoring real positive Perron-Frobenius root $\lambda_1 = \rho(L) > 0$. |
| **RSK-02** | Ill-conditioned modal matrix $P$ leading to numerical instability in spectral decomposition ($L = P D P^{-1}$). | Medium | Low | Condition number check $\kappa(P) < 10^{12}$; fallback to direct matrix multiplication when defective. |
| **RSK-03** | Unicode encoding errors on Windows terminal codepage (CP-1252). | Medium | High | Configured `sys.stdout.reconfigure(encoding='utf-8')` and clean cross-platform ASCII fallbacks. |
| **RSK-04** | Missing external PDF binaries (e.g. wkhtmltopdf). | High | High | Utilized native `matplotlib.backends.backend_pdf.PdfPages` to ensure 100% pythonic zero-dependency PDF generation. |
| **RSK-05** | Negative population values arising from excessive quota harvesting. | Critical | Medium | Enforced non-negativity boundary clipping $\max(x_t, 0.0)$ across all simulation loops. |
