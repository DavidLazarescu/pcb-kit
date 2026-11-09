# House standards (kit default, override per project in `pcb-rules/00-house-standards.md`)

## Tooling
- KiCad 10 and the Konnect MCP server. Invoke the `konnect` skill before any KiCad work.
- Change KiCad files only through Konnect tools. Never text-edit `*.kicad_sch`, `*.kicad_pcb`, `*.kicad_pro`, `*.kicad_sym`, `*.kicad_mod`, `fp-lib-table`, `sym-lib-table`. The kit's hook blocks it; do not work around the hook.
- KiCad (GUI) must not have the file open while an agent edits it, and the user and the agent never edit the same files at the same time. PCB tools need the board open in the PCB editor (IPC); schematic tools are file-based and refuse when the sheet is open.
- Run commands without sudo yourself. Hand only sudo commands to the user.

## Parts
- Supplier: DigiKey. Every part must be in stock, more stock is better. Re-check stock on the order day.
- Assembly in-house by a good assembler: 0603 where possible, 0402 minimum. Exposed pads and leadless packages are fine.
- Fields on every part: `Manufacturer`, `MPN`, `Supplier` = `Digikey`, `Supplier Part` = MPN (with packaging suffix), `Datasheet`.
- Footprints: KiCad standard library (KLC style). Check each footprint against the datasheet land pattern (pitch, pad size, pin numbering, exposed pad). Custom footprints copy the stdlib style: pin-1 mark, courtyard 0.25 mm.
- Symbols: copy a stdlib symbol and adapt it instead of drawing one from scratch.
- Reuse parts from the user's other boards (see `parts-registry.md`) before adding new MPNs.

## Design discipline
- KISS and price. Every part needs a reason. Keep an explicit "removed / kept and why" table.
- Not flight hardware: no over-engineering, but find real failure modes and fix them.
- Plan completely, then build. Record decisions so a new chat can resume from the files alone.
- Ask big, blocking questions early. Decide small style questions yourself.
- All important calculations appear as text notes next to their block in the schematic.

## Documents and language
- Documents are English unless the project overrides it. Explanations to the user follow the user's language, simple, with numbers and ASCII sketches.
- Mark every statement: [V] verified (with source), [A] assumption, [P] pending, [D] decision (who, when), [R] own calculation.
- Anything lasting lives in the repo. Scratch folders vanish with the session.

## Safety net
- Commit before any agent rework of a KiCad project. Never rely on a scratch backup.
- Delegate mechanical lookups (stock, datasheet values) to cheap agents (haiku); keep decisions in the main thread.
- Stackup: JLCPCB default for the layer count; any deviation only after asking the user (see rules/70-layout-plan.md).
