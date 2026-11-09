---
name: pcb-calculations
description: Calculations and simulation for a PCB design: thermal (Tj, heat sink, back-to-back duty), linear-mode MOSFET DC SOA (Spirito), hardware limits, residuals, ngspice with vendor models, loop stability by step response across corners. Use when sizing blocks, checking heat, or simulating a control loop.
when_to_use: Sizing, thermal design, SOA checks, stability analysis or simulation of a circuit block is needed.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/30-calculations-simulation.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/30-calculations-simulation.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Calculations and simulation

Invoke `pcb-workflow` for context. Tools: `${CLAUDE_PLUGIN_ROOT}/tools/thermal.py`.

## Inputs
Requirements, BOM candidates with datasheet values.

## Steps
1. Read the rule layers above.
2. For every block, write inputs, formula, result and margin into `DESIGN.md`. Save repeatable scripts in `calc/`.
3. Thermal: run `thermal.py` with datasheet Rjc, interface Rcs and heat-sink Rsa for the ordered length. Check continuous power, time to limit for single shots, and back-to-back sequences. See [reference/thermal-soa.md](reference/thermal-soa.md).
4. Linear-mode MOSFET: size by power, then check the DC SOA line at the reached case temperature.
5. Compute hardware-enforced limits (supply-limited outputs, divider-limited setpoints) and default-state behaviour at power-up and failure.
6. Compute residuals: leakage, offsets, open-drain pull-downs into high-impedance nodes.
7. Simulate the critical loop with vendor models, see [reference/ngspice.md](reference/ngspice.md). Judge stability by step response over a corner grid, not phase margin alone.
8. Write `sim/RESULTS.md`: final values, why alternatives lost, corner grid, not-converged cases, not simulated, bench test for the first board.
9. Put the key calculations as note texts into the spec (`pcb-schematic-spec`).

## Gate (done when)
- [ ] Every block has a documented calculation with margin
- [ ] Thermal and SOA verified for the worst sequence
- [ ] Hardware limits and power-on state computed
- [ ] Critical loop simulated across corners; `sim/RESULTS.md` written
- [ ] Component values updated in the BOM from the results

## Outputs
`calc/`, `sim/`, `sim/RESULTS.md`, updated `DESIGN.md`.

## Agents
Simulation setup may go to a sonnet agent; decisions stay in the main thread.

## Pitfalls
- Phase margin about 90 degrees for an integrator does not prove a step settles.
- Distributor heat-sink Rth for the wrong length.
- Not stating what the model does not cover (temperature, noise, parasitics).
- Committing vendor models (licence).
