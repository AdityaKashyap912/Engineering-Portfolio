# Landing Gear Dynamics — portfolio copy

This is an unmodified copy of
`engineering_projects/Landing_gear_dynamics/landing_gear_final.py` (the original is never
edited). Run this copy; keep the original as the source of truth.

## What it does

1-DOF oleo-pneumatic main-gear model (`m·s̈ = m·g·(1 − lift) − F_strut`) comparing three
strut designs — fixed orifice (A), metering pin (B), metering pin + longer gas column (C) —
at the design landing, across 12 off-design scenarios, and a 120-case Monte Carlo study.

## Run

```bash
pip install -r requirements.txt
python landing_gear.py
```

Requirements: Python 3 with numpy, scipy, matplotlib, pillow (see `requirements.txt`).

## Outputs (all written to `results/`, resolved from the script's own directory)

| File | Contents |
|---|---|
| `1_design_comparison.png` | Force vs stroke, load vs time, damping profile |
| `2_energy_accounting.png` | Kinetic / gas-spring / damper energy, force components |
| `3_robustness.png` | Peak force vs sink speed, stroke margin, Monte Carlo bottoming-out |
| `landing_gear_animation.gif` | Animation of the three designs at touchdown |
| `scenario_results.csv` | Peak force, stroke, margin and bottoming-out for all 36 scenario/design combinations |
| `results.json` | Nominal metrics, static compression, verification checks, Monte Carlo summary, all scenarios, generation timestamp, file list |

`results.json` is the file the project detail page (`index.html` in this folder) fetches at
runtime via the relative path `results/results.json`, so the website always displays actual
simulation metrics — never hard-coded numbers. Re-running this script regenerates everything
and refreshes the website automatically.
