---
name: pcb-schematic-build
description: Builds a KiCad schematic through the Konnect MCP from a SCHEMATIC_SPEC: commit first, one agent per sheet with fixed reference ranges, connected drawing style, Konnect limits and workarounds (no title block, no rectangles, power symbol names via Value, duplicate #PWR). Use when building or reworking schematic sheets.
when_to_use: The schematic is to be built, extended or reworked from a spec, including delegating to agents.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/50-schematic-build.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/50-schematic-build.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Schematic build

Invoke `konnect` and `kicad-schematic` first; this skill adds the kit's procedure. Style details: [reference/style-and-limits.md](reference/style-and-limits.md).

## Inputs
`SCHEMATIC_SPEC.md`, datasheets, KiCad project created with Konnect (`create_project`).

## Steps
1. Read the rule layers above.
2. Confirm KiCad does not have the files open. Call `list_toolboxes` to confirm Konnect is connected; if not, stop and tell the user.
3. Commit the repository (build and rework both). A scratch copy is not a backup.
4. Create project config (design rules, 0603 defaults, net classes for named nets) with Konnect.
5. Create missing symbols by copying stdlib symbols; check pin numbers against datasheets.
6. Launch one `schematic-builder` agent per sheet in parallel. Each gets: its sheet file, its spec section, its reference range, the style rules, the instruction to touch no other sheet.
7. Build root sheet last (sheet symbols, overview text, pinout tables).
8. Run `pcb-verify` (it is part of the build, not optional). Fix by sheet.
9. Cleanup round: overlapping text, dangling stubs, duplicate `#PWR`, notes legible. Then verify again.
10. Ask the user to set title blocks in the GUI and to review in KiCad.

## Gate (done when)
- [ ] Every spec part placed, fields filled
- [ ] Style rules met (connected, labels between blocks only)
- [ ] `pcb-verify` passed and baseline saved
- [ ] Committed

## Outputs
`.kicad_sch` sheets, PDF render, baseline netlist.

## Agents
`schematic-builder` per sheet, `schematic-verifier` afterwards.

## Pitfalls
- Interrupted agent rework leaves electrically wrong schematics with ERC 0: commit first; after any abort run netcompare against the baseline before anything else.
- Frames drawn with wires create `wire_dangling`.
- Label-scattered circuits read as unconnected.
- Hand-drawn symbols with overlapping pin names.
- User and agent editing the same file.

## Also read
- `${CLAUDE_PLUGIN_ROOT}/rules/45-schematic-review-layout.md` (uniform fields, horizontal text, review structure)
- `${CLAUDE_PLUGIN_ROOT}/rules/41-system-overview.md` (overview PDF, update on structural change)
