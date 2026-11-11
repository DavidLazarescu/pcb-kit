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

## Konnect/KiCad pitfalls found in the first layout (2026-11-11)
- Netclasses written with `create_netclass` go into `.kicad_pro`; an open PCB editor overwrites that file on
  every save. Set netclasses with KiCad closed (or in Board Setup), never while Konnect saves the board.
- Footprints placed by Konnect (`update_pcb_from_schematic`) lose `net_tie_pad_groups`, so net ties show
  clearance errors, and every footprint reports `lib_footprint_mismatch`. Fix in the GUI: Tools → Update
  Footprints from Library (all), then save. Konnect's own library refresh refuses net ties.
- A net tie must not overlap the resistor pad (DRC "shorting items"); place it 0.25 mm off the pad's inner
  edge and join it with a short track that starts at the inner edge.
- Custom rules go into `<board>.kicad_dru` (plain text, Board Setup → Custom Rules). Prove a new rule is
  active by tightening it once and seeing the expected violation, then set it back.
- `kicad-cli pcb render` may show no 3D models; judge orientation from the STEP geometry (colour of
  faces) and the footprint silk marks, and let the owner check in the 3D viewer (Alt+3).
- Courtyards of parts that must touch (a power package against its heat sink) are drawn to the real body,
  so DRC stays clean without exclusions.

## Silkscreen
- Konnect cannot move or hide reference fields or draw silk lines. The pcbnew console script is the route:
  `tools/silkplace.py` plans it, the owner runs it in the open editor (one undo-able action) and saves.
  Never edit the board file as text.
- Reference text 1.0 mm / 0.15 mm, 0.8 mm only where 1.0 does not fit, never smaller. Each reference sits closer
  to its own part than to any other and over no pad. Dense rows of passives get labels on one side in a
  consistent order.
- References and markings must stay readable after assembly: never under a part body (courtyard), heat sink or connector housing.
- Measure text with the ink box (`GetEffectiveTextShape().BBox()`). `GetBoundingBox()` overstates it by about
  15% in width and 50% in height.
- Run Update Footprints from Library before placing references, since its dialog can reset text positions.
- pcbnew SWIG in KiCad 10 does not expose LINE_STYLE: draw dashed silk (for example an isolation barrier) as
  short segments.
- Loop (see `tools/README.md`): plan, apply to a copy, `kicad-cli pcb drc --refill-zones` on the copy, render
  and gridcrop, adjust overrides, hand the console script to the owner.

## Visual checks
- Render a gridded crop of a dense region BEFORE routing or labelling it and again after. A render costs about
  1-2k tokens, far less than DRC iterations. DRC proves clearances, the render judges legibility and routing
  quality; use both.

## More Konnect gaps (first layout)
- No tool deletes vias or zones or changes zone priority; do it in the GUI.
- `add_layer` needs KiCad closed.
- Specctra DSN export refuses boards that already have tracks, zones or custom rules.
