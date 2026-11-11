# Phase 45: schematic readability for review (applies to every build and rework)

A schematic is written for the reviewer. Someone who has never seen the project must be able to
follow it sheet by sheet without zooming around or turning their head.

## Uniform field placement
- One placement rule per part orientation, applied to every part on every sheet:
  - Vertical two-pin parts (R, C, L, fuse, LED): Reference and Value **to the right** of the body,
    Reference above Value, left-aligned, never inside or on the body.
  - Horizontal two-pin parts: Reference **above**, Value **below** the body, centred.
  - ICs and multi-pin symbols: Reference above the top-left corner, Value below the bottom-left corner.
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
