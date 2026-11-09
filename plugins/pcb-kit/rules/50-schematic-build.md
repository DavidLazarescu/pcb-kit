# Phase 50: schematic build

## Procedure
1. Commit the repository state (before any agent build or rework).
2. One agent per sheet, run in parallel, each touching only its own sheet file and its own reference range.
3. Konnect only. Check `list_toolboxes` first; if MCP tools are missing, stop, never fall back to file edits.
4. After the build, run `pcb-verify` before accepting anything.

## Drawing style (connected)
- Parts of one circuit are joined by drawn wires. Same-named local labels inside a block make the circuit look unconnected.
- Labels only between blocks and sheets, at most one label per net per block.
- Pull-ups sit on the bus wires. Decoupling at the IC pin. Dividers inline. Feedback loops drawn as visible loops.
- Signal flow left to right, supplies at the top, grounds at the bottom, A4 sheets.
- Copy stdlib symbols and adapt them. A hand-drawn op-amp symbol had overlapping pin names.
- Calculation notes as text next to their block.

## Konnect limits and workarounds
- No title-block tool and no graphic-rectangle tool. Never draw frames with wires (creates `wire_dangling`). The user sets title blocks in the GUI (File > Page Settings > apply to all sheets).
- `add_power_symbol` cannot set a custom name. Place `power:+5V` or `power:GND`, then change the Value to the net name. In KiCad 10 the Value decides the net. Verify with kicad-cli that islands do not merge.
- Duplicate `#PWR` references across sheets cause annotation warnings. Fix them.
- Loop drawing leaves dangling stubs. ERC shows them; close them.
- The overlap tool reports power symbols at their own pin; that is not an error.
- Schematic tools refuse when the sheet is open in the editor.
- A custom project symbol library is needed for missing symbols; verify pin numbers against the datasheet.

## Agent rework
- An interrupted rework can leave a schematic electrically wrong with ERC 0 (a half-finished rework bridged an isolation barrier). Commit first, and after any abort run netcompare against the baseline before anything else.
