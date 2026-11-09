# Phase 30: calculations and simulation

## Calculations
- Put every calculation into the design document with inputs, formula, result, margin. Copy the key ones into schematic notes.
- Scripts for repeatable math live in `calc/`. The kit's `tools/thermal.py` covers junction temperature, heat sink and back-to-back duty.
- Thermal: Tj = Ta + P x (Rjc + Rcs + Rsa). Take Rsa at the real heat-sink length. Check continuous power, single-shot time to limit, and back-to-back tests with a heat-sink time constant.
- Linear-mode FET: add a DC SOA check (Spirito effect: derate toward high VDS and low current, thermal instability). Use the datasheet DC SOA line at the case temperature reached, not the pulsed curve.
- Hardware limits: compute what the hardware allows even when software writes the worst value (full-scale DAC, shorted output, power-up default).
- Residuals: off-state leakage, offset, bias current into high-impedance nodes.

## ngspice
- Use vendor models for the critical loop. Typical fixes for PSpice models in ngspice:
  - `VSWITCH` to `SW` with VT = (VON+VOFF)/2, VH = (VON-VOFF)/2
  - `TEMP` to `temper`
  - `R_NOISELESS RES(...)` to `R(TNOM=27)`
  - `.spiceinit` with `set ngbehavior=ltpsa`
- Find the DC operating point with source stepping. If the macro model finds a wrong state, select a converged point by a coarse transient and reject runs whose current is not at the set point. List rejected runs; they prove nothing.
- Do not commit vendor models (licence). Document the download URL and the patches in `sim/README.md`.
- Loop gain: break the loop with voltage and current injection (Middlebrook, T = (Tv*Y - 1)/(Y + 1)).
- Stability is judged by step response across corners (source impedance, input capacitance, gain of the pass device, supply) not by phase margin alone. An integrator shows PM near 90 degrees and can still fail a large step.
- Record in `sim/RESULTS.md`: final values, why alternatives lost, corner grid, what converged, what was not simulated (temperature, noise, parasitics), and the bench test to run on the first board.
