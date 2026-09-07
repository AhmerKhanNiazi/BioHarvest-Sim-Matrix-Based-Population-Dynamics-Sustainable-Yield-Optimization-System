# BioHarvest-Sim: Complete Execution & User Guide (رہنما برائے پروجیکٹ)

Yeh guide aapko **BioHarvest-Sim** project run karne, test karne aur evaluate karne ka mukammal tareeqa step-by-step samjhati hai.

---

## 📁 Folder Structure (CCP Folder ke andar kya kya hai?)

```
CCP/
├── core/
│   ├── math_engine.py       # Leslie Matrix, Eigenvalues, Perron-Frobenius, Spectral Decomposition
│   └── optimizer.py         # MSY Linear Programming (scipy.optimize.linprog HiGHS)
├── gui/
│   ├── dashboard.py         # Streamlit Interactive Web Application (Dark Mode)
│   └── presets.py           # 4 Real Species Datasets (Whale, Salmon, Deer, Grizzly Bear)
├── analytics/
│   ├── simulations.py       # Monte Carlo PVA Extinction Risk & Sensitivity/Elasticity
│   └── exporter.py          # PDF Report (PdfPages), CSV Trajectories, JSON Telemetry
├── tests/
│   └── test_math.py         # 17 Automated Unit Tests (100% Pass Rate)
├── main.py                  # Master CLI / GUI Orchestration File
├── requirements.txt         # Project Dependencies
├── README.md                # Comprehensive Mathematical Proofs & Architecture
├── AGILE_PROJECT_DOCS.md    # Agile User Stories (Gherkin), Sprint Metrics & Burn-Down
├── run_gui.bat              # 🚀 Double-click to launch Web Dashboard
├── run_pipeline.bat         # 📊 Double-click to run CLI analysis & generate Reports
└── run_tests.bat            # 🧪 Double-click to run all 17 Unit Tests
```

---

## 🚀 1. Project Run Karne Ka Tareeqa (How to Run GUI)

Aap do aasan tareeqon se interactive dashboard run kar sakte hain:

### Tareeqa A: One-Click Launcher (Sab se aasan)
- `CCP` folder open karein.
- `run_gui.bat` par **double click** karein.
- Browser mein automatically dark-mode dashboard open ho jayega (`http://localhost:8501`).

### Tareeqa B: Terminal / Command Prompt se
Terminal ya PowerShell mein `CCP` directory ke andar yeh command run karein:
```powershell
cd "c:\Users\personal computer\Desktop\Lenear Algebra\CCP"
streamlit run gui\dashboard.py
```
*(Ya phir: `python main.py --gui`)*

---

## 🧪 2. Automated Tests Run Karne Ka Tareeqa (How to Run Tests)

Pure mathematical logic aur constraints ko verify karne ke liye 17 unit tests likhe gaye hain.

### Tareeqa A: One-Click Launcher
- `run_tests.bat` par **double click** karein.

### Tareeqa B: Terminal se
```powershell
cd "c:\Users\personal computer\Desktop\Lenear Algebra\CCP"
python -m unittest discover -s tests -p "test_*.py" -v
```
**Result:** Tamam 17 tests verify honge aur screen par `OK (Ran 17 tests in ~1.8s)` show hoga.

---

## 📊 3. CLI Pipeline Run Karna & Reports Generate Karna

Agar aap pure project ka mathematical summary terminal par dekhna chahte hain aur automatically multi-page PDF, CSV aur JSON files generate karna chahte hain:

### Tareeqa A: One-Click Launcher
- `run_pipeline.bat` par **double click** karein.

### Tareeqa B: Terminal se
```powershell
cd "c:\Users\personal computer\Desktop\Lenear Algebra\CCP"
python main.py
```

Is command se:
1. Charon species (**Fin Whale, Pacific Salmon, White-Tailed Deer, Grizzly Bear**) ka complete analysis console par print hoga.
2. Hard disk par foran yeh files generate ho jayengi:
   - `BioHarvest_Fin_Whale_Report.pdf` (Multi-page formal publication report)
   - `BioHarvest_Fin_Whale_Trajectories.csv` (Time-series data for Excel/R)
   - `BioHarvest_Fin_Whale_Telemetry.json` (Structured parameters & audit log)
   - *(Same for Salmon, Deer, and Bear)*

---

## 🎯 4. University Presentation & Defense Points (Teacher ko kya batana hai?)

Jab aap evaluate hon ya project present karein, to in 4 ahem Linear Algebra topics ko highlight karein:

1. **Leslie Matrix & Perron-Frobenius Theorem:**
   - Population ko age classes mein divide karke transition matrix $L$ banayi gayi hai.
   - Perron-Frobenius theorem ki roo se dominant eigenvalue λ₁ > 0 strictly real aur spectral radius ke barabar hoti hai.
   - λ₁ > 1 ka matlab population grow kar rahi hai, λ₁ < 1 ka matlab decline ho rahi hai (e.g. Grizzly Bear).
2. **Stable Age Distribution ($w_1$) & Fisher's Reproductive Value ($u_1$):**
   - Dominant right eigenvector v₁ ko normalize karke stable age distribution milti hai.
   - Dominant left eigenvector u₁ se reproductive value milti hai (future generation mein kis age class ka sab se zyada hissa hai).
3. **Spectral Decomposition & Fast Trajectory:**
   - $L = P D P^{-1}$ se diagonalize karke $k$-steps trajectory $L^k = P D^k P^{-1}$ se fast calculate hoti hai.
4. **Maximum Sustainable Yield (MSY) via Linear Programming:**
   - Sustainable harvest find karne ke liye SciPy ka HiGHS simplex solver use kiya gaya hai jo objective function max cᵀ · h ko solve karta hai subject to equilibrium condition $(L - I)(L - I) · x* - h* = 0.
5. **Monte Carlo PVA & Extinction Risk:**
   - Real-world environmental stochasticity aur catastrophic disasters (jaise khushksali ya bimari) ko simulate karke 50 saal ka extinction risk calculate kiya gaya hai.
