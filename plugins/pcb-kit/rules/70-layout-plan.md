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
