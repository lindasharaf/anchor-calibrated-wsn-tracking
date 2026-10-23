# Anchors as Live Calibrators

Simulation code for the paper **"Anchors as Live Calibrators: Label-Free Online Conformal Uncertainty for RSSI-Based Target Tracking in Wireless Sensor Networks"** (Linda Sharaf, An-Najah National University).

**Idea.** Every second, each anchor of the wireless sensor network is localized from the other anchors. Because its true position is known, this gives a real localization error measured in the current radio conditions. These errors size a conformal uncertainty circle around the tracked target, with no ground truth for the target. The same inter-anchor measurements detect faulty anchors.

**Main result (50 runs per cell, promised coverage 90%).** After walls appear or propagation drifts, the Kalman ellipse and a one-time survey calibration cover the target 4–11% of the time; this method keeps about 97%. A faulty anchor is detected within 4 s in every run, with no false alarms.

## Requirements
Python 3.10+, `numpy`, `scipy`, `matplotlib`:

    pip install numpy scipy matplotlib

## Run

    python run_all.py        # 8 setups x 50 seeds = 400 runs (~15 min on 2 cores) -> results.pkl
    python run_path2.py      # second trajectory, 4 scenarios x 50 seeds (~2 min) -> results_path2.pkl
    python make_results.py   # tables.md, tables.tex, fig_rolling.png, fig_timeseries_s2.png

All runs use fixed random seeds, so the numbers are reproducible. The saved results are included, so `make_results.py` works without re-running the experiments.

## Files
| File | Content |
|---|---|
| `sim.py` | The world: anchors, log-distance radio model with walls, drift and faults; least-squares localizer; Kalman filter |
| `method.py` | Leave-one-anchor-out self-test, normalized conformal radius, faulty-anchor detector, all compared methods, scoring |
| `run_all.py` | Main experiment (scenarios S1–S4, anchor density 9/16/25) |
| `run_path2.py` | Robustness check on a second trajectory |
| `make_results.py` | Tables and figures of the paper |
| `tra2.npy`, `tra3.npy` | Trajectories from the baseline repository |
| `results.pkl`, `results_path2.pkl` | Saved results of all 600 runs |
| `tables.md`, `tables.tex` | Result tables |

## Credit and license
Built on [abdullahalsaidi16/wsn_localization_tracking](https://github.com/abdullahalsaidi16/wsn_localization_tracking) (GPL-3.0); this code is released under GPL-3.0 as well.
