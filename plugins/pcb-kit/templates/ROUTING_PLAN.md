# <board> layout and routing plan

Written before any placement or trace. No autorouting. Sources: `references/layout-best-practice.md`,
the per-part layout research, DESIGN, SCHEMATIC_SPEC. Tags: [V] datasheet/vendor read, [J] judgement,
[K] general knowledge not re-checked.

## 0. Owner decisions
(Mounting, size limits, connector edges, layer count.)

## 1. Schematic changes before layout (need approval)
(Net ties for Kelvin pairs, mechanical parts as BOM parts, anything the layout research found.)

## 2. Board, stackup, defaults
- Outline, corner radius, mounting holes (plated or not, keep-out).
- Stackup: JLC default for N layers, copper, εr, finish; fab limits with the date read.
- Defaults: track, clearance, copper to edge, via, silk, 45° corners, teardrops.

## 3. Net classes and custom rules
| Class | Nets | Width | Clearance | Notes |
|---|---|---|---|---|

## 4. Ground and return concept
(Quiet plane per island, high-current return copper, the star point, keep-outs.)

## 5. Isolation barrier
(Band position and width with its reason, crossing parts, keep-outs, marking, documented rating.)

## 6. Floor plan
(Orientation-defining parts checked first; ASCII top view with coordinates; signal flow as in the
schematic.)

## 7. Placement groups (in order)
1. Mechanical, locked. 2. Barrier. 3. Power cell. 4. Control loop. 5. Set point. 6. Readback.
7. Supplies and decoupling. 8. Indicators, test points. Then checkpoint A.

## 8. Critical nets and rules
| # | Net / cluster | Rule (width, layer, length, neighbours, loop area) | Source |
|---|---|---|---|

## 9. Order of work
1. Commit; update PCB from schematic; stackup, rules, net classes, custom rules.
2. Outline, holes, mechanical parts, connectors; check orientation in 3D; lock.
3. Placement groups; **checkpoint A**.
4. Zones and pours; check return paths and the star point.
5. Critical nets by hand, each against its row; **checkpoint B**.
6. Remaining nets by hand; tidy.
7. Silkscreen.
8. **Checkpoint C**: `kicad-cli pcb drc` 0 and unconnected 0, netlist against baseline, 3D, independent
   review with the checklist; owner approval before fab outputs.

## 10. Assembly notes
(Torque, solder/screw order, anything the layout implies for assembly.)
