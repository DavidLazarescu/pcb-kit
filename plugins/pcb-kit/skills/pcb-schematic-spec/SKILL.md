---
name: pcb-schematic-spec
description: Writes the SCHEMATIC_SPEC for a KiCad board: per sheet every part with reference, MPN, symbol, footprint, fields and every pin net, reference ranges, global labels, power-net names, calculation notes, style rules. Use when turning a design into an exact build template before building the schematic.
when_to_use: A design is ready to be turned into a buildable schematic specification, or a spec needs revision.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/40-schematic-spec.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/40-schematic-spec.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Schematic specification

Template: `${CLAUDE_PLUGIN_ROOT}/templates/SCHEMATIC_SPEC.md`.

## Inputs
Completed `DESIGN.md` (BOM, calculations, decisions), simulation results.

## Steps
1. Read the rule layers above.
2. Copy the template to `docs/<board>/SCHEMATIC_SPEC.md`.
3. Section 0: project path, sheet list, conventions, field rules, global-label names, power nets (value = net name), reference ranges, repeated-parts table.
4. One section per sheet: a table with reference, part and MPN, symbol (`Library:Name`), footprint, and a connection column naming every pin and net. State "anything not listed is not connected".
5. Name important nets (sense, feedback, high current, critical analog, island grounds) so net classes can target them.
6. Write the exact text of calculation notes for each block.
7. State style requirements: connected drawing, pull-ups on bus wires, feedback loops as loops, labels only between blocks, no frames made of wires, stdlib symbols copied rather than drawn.
8. List library gaps (no symbol or footprint) and which stdlib symbol to copy; custom symbols need pin numbers checked against the datasheet.
9. Check the spec against `DESIGN.md`: every BOM line appears once, every net on critical parts matches, islands never merge, default-state pins are tied as designed. Resolve differences in the documents, not in the build.
10. Choose reference ranges so one agent per sheet cannot collide.

## Gate (done when)
- [ ] Every BOM line placed exactly once with symbol, footprint and fields
- [ ] Every pin of every part has a net or an explicit no-connect
- [ ] Global labels and power nets listed once
- [ ] Notes written with their numbers
- [ ] Spec-versus-design check done

## Outputs
`SCHEMATIC_SPEC.md`.

## Pitfalls
- Specs that describe a circuit loosely: agents invent connections.
- Spec drift from `DESIGN.md`: update both together.
- Missing no-connect decisions on unused pins.
