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

## Process and content (extended 2026-11-11, first real plan; see `references/layout-best-practice.md`)
Research before writing the plan:
- General practice and fab limits: `references/layout-best-practice.md` (sources per rule; re-read the fab's
  capability page on the day and note the date).
- Per part: one research agent reads the **Layout / Layout Guidelines / Layout Example** section of every
  IC and power-part datasheet plus the relevant app notes and returns placement, routing, decoupling,
  thermal and keep-out rules with page numbers, and a critical-net table. Verify its pin numbers against
  the netlist; research agents get pinouts wrong. It also names the **layout example figure** and describes
  where each capacitor sits in it (side of the package, layer, which trace runs under the body, where the
  vias are), and which pins tied to a rail are configuration pins rather than supply or return.

The plan contains, in this order (template `templates/ROUTING_PLAN.md`):
0. Owner decisions (mounting, size, connector edges, layers).
1. **Schematic changes needed before layout**, for approval: e.g. Kelvin sense pairs as their own nets
   via `NetTie_2` at the sense resistor pads (makes DRC enforce the 4-wire connection); mechanical parts
   (heat sink, brackets) as real BOM parts with their footprint and STEP instead of loose holes.
2. Outline, mounting holes, stackup (JLC default, rule above), fab limits with date, our defaults.
   On a board with an isolation barrier the board mounting holes are **non-plated** with a copper
   keep-out, so metal standoffs cannot bridge the grounds.
3. Net classes table and custom DRC rules (`.kicad_dru`), e.g. barrier clearance between net groups.
4. Ground and return concept: one quiet plane per island; high-current returns on their own copper,
   joined to the quiet plane at **one named star point**; keep-outs so THT pins of the high-current path
   cannot touch the quiet plane; no general fill on a layer that carries a same-net power strip.
5. Isolation barrier: band width from the narrowest crossing part's pad gap and the working voltage,
   only rated parts cross, nothing else in the band, silk marking, the rating actually documented.
6. Floor plan (ASCII, top view, coordinates) following the schematic signal flow. **Check the
   orientation-defining parts first** (power package tab side, connector pin 1) in the footprint/3D,
   because they decide which side the gate, source and sense circuits land on.
7. Placement groups in order (mechanical → barrier → power cell → control loop → set point →
   readback → supplies → indicators/test points).
8. Critical-net table: every net from the design notes and the per-part research with rule and source.
   Followed by a **capacitor table**: every capacitor with the IC it serves, its tier (rule 80, *Capacitor
   placement*), the datasheet figure it follows, and the IC's real supply and return pins. These rows become the
   `--tier` and `--pins` arguments of `tools/capcheck.py`.
   Prefer high-current paths that stay on one layer between THT pads (no vias), and route the sensitive
   net across a high-current path on the opposite layer.
9. Order of work with checkpoints A (placement), B (critical nets), C (complete) — see rule 80.
10. Assembly notes that come out of the layout (torque, order of soldering and screwing).

11. Decide the layer count from routing density before placement: count the slow cross-connections
    that must cross critical clusters. If a 2-layer board would route them on the ground layer, propose
    4 layers early (the JLC 4-layer cost delta is small for small boards) instead of discovering it
    during routing.
