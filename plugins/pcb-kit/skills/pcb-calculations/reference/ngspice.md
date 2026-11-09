# ngspice with vendor models

Setup
1. Download the vendor PSpice model; keep it out of the repo (licence). Document URL and fixes in `sim/README.md`.
2. Fixes for ngspice: `VSWITCH` to `SW` (VT = (VON+VOFF)/2, VH = (VON-VOFF)/2); `TEMP` to `temper`; `R_NOISELESS RES(T_ABS=...)` to `R(TNOM=27)`; `.spiceinit` with `set ngbehavior=ltpsa`.
3. DC operating point by source stepping. Macro models can settle in a wrong DC state; choose a converged point by a coarse transient and reject runs where the current is not at the set point.

Analyses
- Loop gain: break the loop, inject voltage and current (Middlebrook), T = (Tv*Y - 1)/(Y + 1).
- Step response over a corner grid: source voltage and impedance, input capacitance, pass-device transconductance corners, threshold corners, supply, cable inductance. Large and small steps, up and down, from zero.
- Off state and failsafe: DC at code zero with offset corners, and with faulted setpoint nodes.
- Report: overshoot, settling (2 % band), ringing, residual current at off.

Judgement
- An integrator-like loop shows PM near 90 degrees for any compensation; the step test is what decides. A compensation value that looks fine in AC failed a large step.
- No device model for the power part: fit a generic model to datasheet points (gfs, Ciss, Crss, Coss, RDS(on), Vth) and scale gfs over corners; state that the low-current behaviour is unknown.
- List not-simulated items and cases that did not converge. They are not evidence of stability.
- Generate netlists with a script, keep `runall.sh`, keep result files.
