---
name: pcb-layout
description: PCB placement and routing with Konnect following a written routing plan: fixed parts first, critical nets by hand, rest by hand to a clean standard, no blind autorouting, DRC and independent review. Thin skill, to be extended after the first layout. Use when placing parts or routing traces.
when_to_use: A routing plan exists and the board is to be placed, routed, or checked.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/80-layout.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/80-layout.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Layout

Status: thin, to be extended after the first layout. Invoke `konnect` and `kicad-pcb` first.

## Inputs
`ROUTING_PLAN.md`, verified schematic.

## Steps
1. Read the rule layers above. Refuse to start without an approved plan.
2. Confirm KiCad is running with the board open in the PCB editor (IPC) and the user does not edit it. Commit first.
3. Update the PCB from the schematic; set outline, holes, keep-outs, isolation gaps on all layers.
4. Place fixed parts (connectors, isolating parts), then critical clusters, then the remaining groups, then decoupling at the pins, then LEDs, test points.
5. Create zones and planes; check return paths.
6. Route critical nets by hand with Konnect track and via tools; check each against its plan rule after routing.
7. Route the rest by hand: consistent widths, 45 degree corners, no acute angles, no stubs, parallel buses aligned, few vias, tidy fanouts, stitching vias.
8. Silkscreen: connector pin labels, indicator labels, barrier marking, board name, version, date.
9. DRC 0. Independent review (`kicad-design-review-agent` or a fresh agent) against the plan.
10. Freerouting only as a reviewed draft for non-critical leftovers.

## Gate (done when)
- [ ] All critical nets match plan rules
- [ ] DRC 0
- [ ] Independent review done and findings closed
- [ ] Committed

## Pitfalls
- Blind autorouting.
- Editing the board in the GUI while an agent works.
- Isolation gap violated by pours, vias or test points.
- Return paths crossing the island split.
