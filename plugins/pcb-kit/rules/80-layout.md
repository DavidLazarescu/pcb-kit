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
  `tools/silkplace.py` plans it, the owner runs it in the open editor and saves (console edits are not undoable; File > Revert discards them).
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

## Owner review of the first board, round 2
- **3D models are checked by eye before handover.** Render top and tilted
  (`kicad-cli pcb render --side front --perspective --rotate '40,0,0'`) and look at every custom or
  downloaded model. Vendor STEP files from SolidWorks are often drawn Y-up: the part lies on its side and needs
  rotate X 90° plus a Z offset of half its height. Fix it in the library footprint and update the board from
  the library, so the fix survives.
- **Decoupling first, routing second.** Capacitors are placed before the signals around them are routed. A
  signal is routed around a capacitor; a capacitor is never moved away to make a route prettier. The full
  rule is the section *Capacitor placement* below.
- **Test points are labelled with the signal**, not the reference: the silk next to a test point reads
  `GND`, `GATE`, `I_SET`, and the TP reference is hidden. No separate test-point legend table, because looking
  up a table while probing is overhead.
- **Indicators are labelled with their function** (`PWR`, `HOT`, `ALERT`) directly next to the LED; the LED
  reference is hidden like any passive.
- **A pad that a zone feeds lies completely inside the zone outline.** A zone outline cutting through a pad
  looks like an error even when the fill joins it; draw the outline around the whole pad.
- **As few layers as reasonable.** Route signals on the outer layers. Inner layers are planes; a trace on a
  plane layer needs a stated reason in the routing plan, and a single stray trace there has none.
- **As few zones as possible.** Every zone has a reason written in the routing plan. Do not repair a plane
  with patch zones; change the main outline or the keep-out instead.
- **45° corners only**, no 90° corners and no arcs mixed in. Check every corner by script before handover
  (angle between consecutive segments of a net on one layer), not only by eye.

- **Teardrops only on clean joints.** A teardrop grown on a bad joint (pad to pad, a via squeezed between
  pads, a short stub into a tab) becomes an odd blob that reviewers read as an unreliable connection. Fix the
  geometry first, then generate teardrops (house standard), and look at them before handover. A teardrop never
  patches a joint.
- **A track enters a pad end-on, from the pad centre.** Never let a track slide along a pad edge or end at the
  pad rim with a sliver of overlap; a T-junction belongs on the track, away from the pad.
- **One via per pad.** Two pads never share a via placed between them; each pad gets its own via straight
  out from its centre. A via never "touches" a track to connect; join it with its own stub.
- **Pours are proper polygons.** A copper area that joins pads (source to shunt, regulator tab) is a polygon
  drawn around the pads it serves, with 45° sides and a solid pad connection, not a rectangle cutting through
  a pad and not tracks dressed up with teardrops.
- **Check every joint by script before handover** (`tools/joints.py`): a reviewer who finds one sloppy joint
  will find the same pattern elsewhere, so fix the pattern board-wide, not only the spot that was marked.
- **After removing parts, look for what they left.** A via that joined the removed part to a plane survives a
  dangling-copper clean-up because it still joins two planes, often with a few tenths of a millimetre of dead
  track. DRC and the unconnected list stay silent. `joints.py` lists vias whose tracks lead nowhere and vias
  joined only by zones with the zone names; every one that only joins the planes and has no stated stitching
  purpose goes.
- **Isolation is checked across layers, projected.** A plane of the isolated side must not reach under the
  port side on another layer: an inner plane 0.2 mm below a port pad is as close as its prepreg, not as far as
  the same-layer DRC says. Keep the barrier band free on every layer and run `tools/isocheck.py` (all port
  copper against all isolated copper, every layer, projected) before handover.

## Capacitor placement (owner review 2026-11-16)
Capacitor placement is checked first and hardest, because it is where a layout most often looks routed but
works worse than the datasheet's own board. The owner found a charge-pump flying capacitor reached through two
vias and a B.Cu detour, and an output capacitor whose ground pad pointed away from the IC with its via
2 mm off. Neither failed DRC. Trying placements is cheap for an agent, so try several and measure them; do
not settle on the first that routes.

**The current loop is what counts.** For every capacitor, follow the copper from the IC supply pin through
the capacitor back to the IC's own return pin. Keep that loop short and small. Vias add inductance to it,
and a return that has to cross the package adds area.

**Strictness follows what the loop carries.** Each capacitor gets a tier in the routing plan (§ critical
nets):
| Tier | Which capacitors | Rule |
|---|---|---|
| 1 | Switching and charge-pump loops: flying, input and output capacitors of converters, gate-drive bootstrap, anything carrying fast pulsed current | Datasheet layout example followed exactly. **No via** in a signal leg (a flying capacitor has two). All capacitors on the IC's layer, joined by top copper; input and output returns meet at one point next to the IC ground pin. |
| 2 | Supply pins of ICs, references (VREF, VREFIO), ADC/DAC, amplifier and sensor supplies, input filter capacitors at an amplifier | At the pins, no via in the signal leg. The ground pad faces the IC ground pin where the supply and ground pins are neighbours; otherwise it gets its own via right at the pad, as the datasheet examples draw it. |
| 3 | Bulk and entry capacitors, a second capacitor of the same size behind the first, pull-ups | Near the rail they serve, reported but not failed. No effort spent beyond tidy routing. |

**Read the datasheet's Layout section before placing**, and copy its topology, not just "close to the pin":
which layer, which side of the package, which trace runs under the body, where the via sits. Record each
IC's figure (e.g. "LM2665 Figure 17") in the routing plan. A deviation is allowed when it is measured better
on this stackup (a 4-layer board with ground directly under the top can beat a 2-layer example), and the
reason goes into the plan.

**Practical points from the first review:**
- A trace under the package body is often the datasheet's answer: a SOT-23-6 charge pump with CAP+ and CAP−
  on opposite corners reaches its flying capacitor on top by running CAP− between the pin rows.
- Two capacitors of the same package in parallel: the one the datasheet names (the CIN or COUT carrying the
  charge) goes closest. A 100 nF of the same size behind it gains no ESL.
- A pin tied to a rail for configuration (shutdown, address, interface select) is not a supply or return
  pin. Give it its own via and do not count it as the IC's ground.
- Fine-pitch supply and ground pins next to each other (MSOP VS/GND): put the capacitor beside the pins
  with direct top tracks to both, not below the package with a plane hop.
- An IC ground pin may reach the plane through the ground pad and via of its own capacitor; that is still
  one via per pad.

**Measure, do not judge by eye.** `tools/capcheck.py BOARD --tier IC=1 ... --pins IC=n,n` follows the real
copper (pads, tracks, vias, zone fill) for every capacitor and fails a row on vias in a signal leg, a
ground via far from its pad, a loop longer than 2× (tier 1) or 2.5× (tier 2) the ideal for that pin pair,
or a ground pad facing away. Its score compares variants of the same board. Workflow: build each candidate
placement as a copy of the board by script, run `capcheck.py`, DRC and `joints.py` on each, keep the best,
note the rejected variants and their numbers in the plan. Run it at checkpoint A (placement) and again
before handover. A capacitor that fails stays failed until it is moved or its tier is changed with a reason
in the plan.

## pcbnew API on a closed board (KiCad 10, Python 3.14)
- Check for `~*.kicad_pcb.lck` / `~*.kicad_pro.lck` right before every write, not once per session: the owner may open
  the project in between, and a later save from the GUI silently overwrites the scripted changes. Put the check in the script.
- With KiCad closed, `pcbnew.LoadBoard` / `SaveBoard` edit the board through KiCad's own serializer (not a text
  edit). Work on a copy first, `kicad-cli pcb drc --refill-zones` it, then repeat on the real file and commit.
- `ZONE.SetOutline()` keeps a pointer to the Python-owned polygon and crashes the filler later: edit
  `zone.Outline()` in place (`RemoveAllContours`, `NewOutline`, `Append`).
- After `BOARD.Remove()` the SWIG iterators of that process can break (`SwigPyObject is not iterable`): collect
  everything first, remove just before saving, and split multi-phase edits into separate processes.
- Removing a via or track leaves its teardrop zone behind and the zone filler segfaults: remove teardrop zones
  of the same net that touch the removed ends (or remove all of them and regenerate in the GUI after the edit; the Python API cannot generate teardrops).
- A footprint loaded with `FootprintLoad(dir, name)` has no library nickname: set `SetFPID(LIB_ID(nick, name))`,
  `SetPath`, `SetSheetname` and `SetSheetfile`, then confirm with `kicad-cli pcb drc --schematic-parity`.
- Footprint 3D model settings: change `fp.Models()[i].m_Rotation = VECTOR3D(...)` by index; assigning to the
  fields of an iterated copy does nothing.
- Load, edit and save one board per process. After `Save`, `FindFootprintByReference` and a second `LoadBoard`
  in the same process return bare SWIG objects (`no attribute 'Pads'`, `'BuildConnectivity'`): run the zone
  fill as its own process.
- Footprint fields in KiCad 10: `GetFieldByName` is gone; pick the field from `fp.GetFields()` by `GetName()`.
