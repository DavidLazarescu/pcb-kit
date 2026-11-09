---
name: pcb-layout-plan
description: Writes the PCB routing plan before any placement or trace: stackup and layer roles, ground and return concept, isolation gaps, placement groups, critical nets with rules, defaults, order of work, verification. Thin skill, to be extended after the first layout. Use when starting PCB layout.
when_to_use: The schematic is verified and layout is about to start, or a routing plan is requested.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/70-layout-plan.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/70-layout-plan.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Layout plan

Status: thin, to be extended after the first layout. Template: `${CLAUDE_PLUGIN_ROOT}/templates/ROUTING_PLAN.md`.

## Inputs
Verified schematic, requirements (size, connectors, isolation), calculations (currents, thermal).

## Steps
1. Read the rule layers above.
2. Board: outline, corner radius, mounting holes (none inside an isolation gap), connector edges.
3. Stackup: layer count and role per layer. Typical 4-layer: L1 parts and short signals, L2 solid ground (split per island), L3 supply pours, L4 signals and ground fill.
4. Ground and return: solid planes, one plane per island, each return path stays under its signal on its own side.
5. Isolation: gap width on all layers, only the isolating parts cross, no copper, via, test point or hole inside, silkscreen marking.
6. Floor plan: ASCII sketch with signal flow in the schematic's direction, groups, connectors at edges, noisy parts (switching converters) away from precision analog.
7. Critical nets and rules (width, clearance, length, loop area, neighbours): feedback loops as tight clusters around the amplifier, high-impedance inputs short with solid ground below, references with caps at the pins, sense nodes Kelvin-routed, high-current paths wide and short, supplies decoupled at the pins, bus pairs routed through the logic zone only.
8. Defaults: signal and supply widths, clearance with margin over the fab minimum, via size, 45 degree corners only.
9. High-current and thermal: copper width for current, pad-to-sink copper, sensor placement at the heat path.
10. Order of work (see `pcb-layout`) and verification: DRC 0 plus independent review.
11. Name net classes for named nets via Konnect design rules.
12. Get user approval of the plan.

## Gate (done when)
- [ ] Plan covers stackup, ground/return, isolation, groups, critical nets, order, verification
- [ ] Every critical net from the design has a rule
- [ ] User approved

## Outputs
`ROUTING_PLAN.md` (or a DESIGN section).

## Pitfalls
- Starting placement before the plan exists.
- Autorouting as the plan.
- Critical nets found only during routing.
