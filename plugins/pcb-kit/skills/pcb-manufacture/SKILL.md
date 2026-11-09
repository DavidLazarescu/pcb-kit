---
name: pcb-manufacture
description: Release checklist for a KiCad board: re-check DigiKey stock on the order day, lifecycle, spares, BOM fields, footprint re-check, DRC and review, fab outputs via the kicad-manufacture skill, first-board bench tests. Use when preparing to order or send to fab.
when_to_use: The user wants to order parts or boards, generate fab files, or asks if the board is ready for fabrication.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/90-manufacture.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/90-manufacture.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Manufacture

Invoke `kicad-manufacture` for the output generation; this skill adds the order-day checks.

## Inputs
Verified schematic, DRC-clean board, BOM.

## Steps
1. Read the rule layers above.
2. Re-run stock checks for every MPN (agent `part-researcher`). Compare to the BOM date; list changes and substitutes.
3. Check lifecycle: Not-For-New-Designs and last-time-buy dates; order spares together with the main order.
4. Confirm BOM fields and DNP flags; export the BOM.
5. Re-check custom and variant footprints against datasheets.
6. Confirm DRC 0, independent review closed, silkscreen labels present.
7. Match fab rules to project config; generate gerbers, drill, position file via `kicad-manufacture`.
8. Save release outputs and the schematic baseline in the repo; commit and tag.
9. Write the first-board bench tests (from `sim/RESULTS.md`) into `DESIGN.md`.

## Gate (done when)
- [ ] Stock confirmed on the order day
- [ ] Spares ordered for end-of-life parts
- [ ] Outputs generated and committed
- [ ] Bench test list written

## Agents
`part-researcher`.

## Pitfalls
- Planning-day stock numbers reused on the order day.
- Missing packaging suffix in the order MPN.
