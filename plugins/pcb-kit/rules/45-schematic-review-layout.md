# Phase 45: schematic readability for review (applies to every build and rework)

A schematic is written for the reviewer. Someone who has never seen the project must be able to
follow it sheet by sheet without zooming around or turning their head.

## Uniform field placement
- One placement rule per part orientation, applied to every part on every sheet:
  - Vertical two-pin parts (R, C, L, fuse, LED): Reference and Value **to the right** of the body,
    Reference above Value, left-aligned, never inside or on the body.
  - Horizontal two-pin parts: Reference **above**, Value **below** the body, centred.
  - ICs and multi-pin symbols: Reference and Value **stacked as one block** (Reference on top, Value
    directly below it) right at the body, at a corner that has free space, within one or two grid steps.
    Never split them to opposite corners and never let them drift away from the body: the reader must
    see at once which part number belongs to which reference.
  - Connectors: Reference above, Value (part number) below.
  - Power symbols and labels: KiCad default, readable from the bottom.
- Same spacing between body and text everywhere (one grid step, 1.27 mm).
- Hidden fields (MPN, Supplier, Footprint, Datasheet) stay hidden on the sheet; they live in the BOM.

## Text orientation
- **All text reads horizontally, left to right, from the bottom of the page**: references, values,
  net labels, notes, headings. No rotated (90°/270°) field text, also on vertical parts.
  Rotate the field, not the part, when a part is drawn vertically.
- Pin numbers and pin names come from the symbol and may stay as KiCad draws them.

## Structure for review
- One functional block per area, a heading above it, signal flow left to right, supplies up,
  grounds down; blocks separated by clear space (≥ 10 mm).
- The calculation note sits next to its block, aligned with it, short lines (≤ ~100 characters).
- Repeated structures (channels) are drawn identically, with the same relative placement.
- Before handing over: render every sheet at 4200 px width, cut it into 12 tiles
  (`magick full.png -crop 4x3@ +repage tile_%02d.png`), read every tile and log each defect; fix and
  repeat until a full round finds none. An overview-zoom look misses overlaps (a reworked sheet passed
  that way with overlapping pin names, colliding values and parts at the frame). Overlap tools alone are
  not enough either.
- Defects: text touching text, wires, pins or bodies; pin names overlapping inside a symbol; anything
  within 5 mm of the frame or in the title block; fields closer to another part than to their own;
  wire crossings that read as junctions; op-amp/comparator inputs without + and -.
- A builder's own "checked" is not acceptance: a different agent or the user reviews the tiles.

## Symbols: clean and simple
- Symbols are drawn for understanding, not for completeness: clean outline, pins grouped by function
  (inputs left, outputs right, supplies top, grounds bottom), short readable pin names, no decorative
  detail. Find the middle: as simple as possible while every pin stays unambiguous.
- Prefer the KiCad stdlib symbol (or a copy of it) over a hand-drawn one; if a custom symbol is
  needed, model it on the stdlib style of the same device class (op-amp triangle, regulator box, …).
- Render every custom symbol once on its own and check that pin names and numbers do not overlap.

## Sheet split along the signal chain (review feedback, 2026-11-11)
- Split sheets by signal chain, not by part type. A part that measures, drives or protects another part
  sits on the same sheet, next to it: the current monitor next to its shunt, the gate driver next to the
  MOSFET, the protection circuit next to what it switches off.
- A reviewer must be able to follow one function (e.g. set point → control loop → power stage → shunt →
  readback) on one sheet without jumping pages; cross-sheet labels only between functions.

## Note texts on the sheets (review feedback, 2026-11-11)
- A note explains what a reader would otherwise not understand: why a block exists, why a value was
  chosen, what happens in a fault. Nothing the symbols already show.
- Short: 1–4 lines per block, plain sentences. Lead with the purpose ("Turns the load off at 80 °C
  heat-sink temperature, back on below 75 °C.").
- Math only for non-trivial, decision-relevant results, and then only the result with its key inputs
  ("Threshold 9 V: normal gate ≤ 5.2 V at 3 A, simulated"). No derivations, no unit bookkeeping,
  no restating datasheet defaults. Full calculations live in DESIGN.md; the note may point there.
- Same wording style on every sheet; no session history ("changed on …", "review …") in notes.

## Readability (owner review of the first board)
- The main current path is one straight line; sense and Kelvin taps branch off sideways through their net ties.
- Decoupling capacitors in electrical order along the rail: the 100 nF next to the supply pin, bulk capacitors further out.
- Incoming connectors face into the circuit; power pins at the top, ground at the bottom.
- No text over text, wires or symbols; a label sits on a short stub, never across a wire. BOM-only parts (screws, insulators) get their own block.
- Same net name on both sides of a pass-through part (ESD arrays with internally joined pins); different names only across a series element.
- After every edit render the sheet and look at it. When rotating or redrawing net ties, compare the netlist with the baseline: a pin swap changes the pad nets on the board.

## Spacing, alignment and blocks (owner review of the first board, round 2)
- **Breathing room at every connection.** Between a pin end (part or power symbol) and the next junction,
  corner or wire it joins, keep at least one grid step (2.54 mm) of plain wire. A capacitor hanging from a
  rail gets a vertical stub from the rail to its pin, the same as the stub from its other pin down to the
  ground symbol; a rail must never run straight into a pin end. Generous, not wasteful: one or two steps.
- **Align power symbols.** Within a block, ground symbols sit on one horizontal line and supply symbols on
  one line, wherever the parts allow it (extend the shorter stubs). Ragged ground heights read as noise.
- **Blocks.** Split each sheet into a few logical blocks (set point, control loop, power stage, readback,
  supply, isolation, protection …), not finer than a reader thinks in. Each block has a heading, clear space
  (≥ 10 mm) to its neighbours, and ideally a frame; signals between blocks go through net labels at the block
  edge instead of long wires across the sheet. Konnect cannot draw rectangles: leave the frames to the GUI
  (Place → Rectangle, one per block) and say so in the handover.
- **Align labels and ports that belong together.** A bus or a pair (SDA/SCL, a sense pair, supply rails into
  a block) stacks vertically at the same x, one grid step apart, in pin order.
- **PWR_FLAG points up**, standing on a short stub above the rail, like a supply symbol. Hang it below the
  rail only where the space above is taken (for example at a connector pin row).
