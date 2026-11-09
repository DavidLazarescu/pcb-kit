# Phase 70: layout plan (to be extended after the first layout)

Write the routing plan before any placement or trace. Content:
1. Board outline, mounting holes, stackup and role of each layer.
2. Ground and return-current concept (solid planes, split planes per island, where returns flow).
3. Isolation gaps: width, on all layers, nothing crossing but the isolating parts' bodies.
4. Placement groups and signal flow (same direction as the schematic), connectors on edges.
5. Critical nets with rules: width, clearance, length, loop area, neighbours to avoid.
6. Defaults: signal and supply widths, clearance, vias, 45 degree corners.
7. Order of work.
8. Verification: DRC 0 plus independent review.
No blind autorouting at any point.

## Stackup (house rule)
- Use the **JLCPCB default stackup** for the chosen layer count (standard FR-4, 1.6 mm, standard copper
  weights, JLC's default prepreg/core build). Name the exact JLC stackup in `ROUTING_PLAN.md` and set it up
  in KiCad's Board Setup → Physical Stackup with JLC's published thicknesses and dielectric constants
  (take them from JLC's stackup / impedance page at the time of design, with the date; do not use generic
  values).
- Anything else — other thickness, heavier copper (e.g. for high current), more layers than needed,
  special material, controlled-impedance order option — is **discussed with the user before** it goes
  into the plan, with the reason and the cost impact.
- Impedances (USB, Ethernet, RF, fast single-ended) are calculated with that JLC stackup (JLC impedance
  calculator or KiCad's calculator with the same parameters); trace widths/gaps go into net classes and
  the routing plan with the calculated value and the source.
- High-current traces are sized for the default copper weight (IPC-2152 with the stated temperature
  rise); if the default copper is not enough, that is a discussion with the user, not a silent change.
