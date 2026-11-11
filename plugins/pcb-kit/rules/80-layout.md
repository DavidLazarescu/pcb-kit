# Phase 80: layout (to be extended after the first layout)

- Needs KiCad running with the board open in the PCB editor (IPC). Nobody else edits the board meanwhile.
- Follow the written routing plan. Place fixed parts first (connectors, isolating parts), then critical clusters, then the rest, then decoupling at the pins.
- Critical nets by hand first. Then the rest by hand: consistent widths, 45 degree corners, no acute angles, no stubs, aligned buses, few vias, tidy fanout, stitched pours, readable silkscreen.
- Freerouting only as a reviewed draft for non-critical leftovers, never as the result.
- Check each critical net against the plan after routing it.
- Finish with DRC 0 and an independent review by a different agent.
- Commit before each large automated step.

## Gates and checkpoints (extended 2026-11-11)
- Agent self-reports are not evidence. Published tests of LLM-driven KiCad routing found every session
  claiming completion while 1-8 nets were routed (`references/layout-best-practice.md` §1.2). Each step
  ends with a deterministic check whose output gates progress: `kicad-cli pcb drc` (with zones refilled)
  for violations and unconnected items, courtyard overlaps, the netlist against the schematic baseline.
- Feed the analysis structured data (coordinates, pad lists, DRC JSON), use renders for the visual
  judgement and for the owner, not as the only check.
- Work in small batches (one group or one critical net), re-read the board state from the file after
  each batch, commit after each checkpoint.
- **Checkpoint A** after placement (no traces yet): courtyards 0 overlap, 3D view, ratsnest crossings
  reviewed, critical clusters measured against the plan, owner looks at the render.
- **Checkpoint B** after zones and critical nets: each critical net checked against its plan row
  (width, length, neighbours, layer), DRC run.
- **Checkpoint C** complete: DRC 0, unconnected 0, netlist matches, 3D top/bottom, independent review with
  the checklist in `references/layout-best-practice.md` §8, then fab outputs only after owner approval.
- Placement revisit gate: if routing congests one region, move parts instead of forcing routes.
