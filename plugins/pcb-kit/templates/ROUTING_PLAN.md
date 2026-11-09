# <board> layout and routing plan

Written before any placement or trace. No blind autorouting.

## 1. Board, stackup, layer roles
- Outline, corner radius, mounting holes.
- Layers: L1 / L2 / L3 / L4 roles.
- Defaults: signal width, supply width, clearance, vias, 45 degree corners.

## 2. Ground and return concept

## 3. Isolation gaps
(Width, layers, what may cross, marking.)

## 4. Floor plan
(ASCII sketch, signal flow as in the schematic.)

## 5. Placement groups

## 6. Critical nets and rules
| # | Net / cluster | Rule (width, clearance, length, loop area, neighbours) |
|---|---|---|

## 7. High current and thermal

## 8. Order of work
1. Update PCB from schematic; outline, holes, keep-outs.
2. Place fixed parts, critical clusters, groups, decoupling, LEDs, test points.
3. Planes and pours; check returns.
4. Critical nets by hand; check each against section 6.
5. Remaining nets by hand; tidy.
6. Silkscreen.
7. DRC 0, independent review, fab outputs.

## 9. Verification and approval
