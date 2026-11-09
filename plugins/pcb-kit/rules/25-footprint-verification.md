# Footprint verification (phases 20, 40, 60, 80, 90)

A wrong footprint must never reach a PCB order. Scripts decide, the model reads only failures.

## Three layers

1. **L1, automatic, every part.** Make or reuse the record `parts/<MPN>.yaml` (see `parts/README.md`), then run `tools/fpcheck.py` per part (pads, pitch, sizes, exposed pad, drill, pin 1, hash, and with the netlist every symbol pin name against the datasheet pin table). In layout add `kicad-cli pcb drc --format json --schematic-parity --severity-all`. `check_footprint.py` from kicad-library-utils (KLC) is optional for stdlib-style footprints.
2. **L2, independent second source, once per part.** Compare the footprint with a manufacturer CAD download, SnapEDA or Ultra Librarian using `tools/fpdiff.py` (any transform except identity is a flag), and check the IPC-7351B envelope. Add `second_source` to `verified.layers`.
3. **L3, before the order.** Export STEP (`kicad-cli pcb export step --include-pads --subst-models`) and view it in 3D, check the fab CPL and DFM preview rotations, print the PCB 1:1 on paper and lay the real parts on it for **every high-risk part**. A human signs off; add `physical` to `verified.layers`.

## High risk

SOT-23, SOT-223 and DPAK transistors and regulators; ambiguous package names (SOIC narrow or wide, MSOP or VSSOP, DGS or DGK, QFN and DFN variants); exposed pads; connectors (mating side, drill); polarised parts; fine pitch; any custom or third-party footprint; anything without a record. High-risk parts need all three layers.

## 3D model for every footprint

Each footprint references a 3D model that exists. Sources in order: the KiCad 3D library (`/usr/share/kicad/3dmodels`), a manufacturer STEP downloaded by the user (when sites block or need a login), a SnapEDA or Ultra Librarian package, and as last resort a simple box with the body dimensions. Project models live in `<project>/3dmodels/` and are referenced as `${KIPRJMOD}/3dmodels/<name>.step`. Exceptions are explicit (mounting holes): list the footprint name in `<project>/3d-exceptions.txt`. `bom_fpcheck.sh` reports `MISSING-3D` otherwise.

## When it runs

- Phase 20: record and `fpcheck` when the footprint is assigned; every part has a verified record or is listed as pending.
- Phase 40 and 50: again after the schematic is built (pin names are checked from the netlist).
- Phase 80: again in layout, plus DRC with schematic parity.
- Phase 90: `tools/bom_fpcheck.sh <project>` all PASS, plus L3 sign-off. The order is blocked otherwise.

## Token economy

A record is made once per MPN: read only the package and pinout pages of the datasheet (`pdftotext -f N -l N`), store the result in the registry, reuse it in later projects. Re-verify only when the footprint hash or the datasheet revision changes. Read the script output only where it says FAIL. Overlays of footprint over drawing are a last resort.

## Self-built footprints: what the blind test showed (2026-11-09)
Seven footprints were built from datasheets alone and compared with `fpdiff.py` against the KiCad stdlib:
SOIC-16W exact; VSSOP-10 ×2, SOT-23-5, SOIC-8 within 0.1–0.2 mm (manufacturer land vs IPC nominal,
both valid); TO-247 pad centres exact (drill 1.9 mm, larger than stdlib's 1.5 mm — the stdlib hole is
tight for the worst-case lead). **One real error:** SOT-223 tab numbered as pad 4 instead of pad 2,
which would have left the tab unconnected. Geometry from a datasheet is reliable; numbering conventions
are where self-built footprints fail. Cost ≈ 15–20k tokens per footprint.
Consequences:
- Order of sources stays: stdlib → manufacturer download → self-built.
- A self-built footprint always gets a record + `fpcheck` (catches extra/missing pads), an `fpdiff`
  against any second source, and the 1:1 print.
- Checklist for self-built: tab / exposed pad carries the number of the pin it is tied to; pin 1 at the
  top left in the default orientation; pad numbers exactly as the datasheet pinout; IPC nominal density
  unless the datasheet gives a land pattern; courtyard 0.25 mm; fab outline = body.
- `fpdiff` compares pad sets: if pad counts differ, fix numbering first, then compare geometry again
  (centroid normalisation is skewed by extra pads).

## Footprint intake with the user (before layout and on every additive iteration)
1. **Request list.** Before the layout starts, and whenever parts are added later, run
   `bom_fpcheck.sh` and `fp_requests.py --generic-ok` and give the user `FOOTPRINT_REQUESTS.md`:
   every part without a verified record, with a failing check or without a 3D model, and what is needed
   (datasheet, manufacturer footprint/zip, STEP). Footprints the stdlib already has only need the datasheet.
2. **User downloads** into `<project>/libs/downloads/<MPN>/`.
3. **Claude imports and checks every download:** footprint into the project library
   `<project>/libs/<board>.pretty` (Konnect), STEP into `<project>/3dmodels/`; make the part record from
   the datasheet; `fpcheck` (geometry, numbering, pin names, 3D present); `fpdiff` against the stdlib
   footprint when one exists; 3D model aligned with the pads.
4. **Verdict per part:** ACCEPTED → use it, record `verified.layers` updated. REJECTED → tell the user in
   that step with the reason (e.g. "tab numbered 4, datasheet ties it to pin 2", "pitch 0.65 vs 0.5")
   and what would fix it (other source, or a self-built footprint per the checklist). Never use a
   rejected footprint and never fix a download silently.
5. Standard chip passives (R/C/L 0402…2512 on stdlib footprints) are covered by generic chip
   records; fuses (package sizes vary per series), LEDs and diodes still need their polarity (cathode pad) checked per MPN.
6. The layout phase may not start while the list has open entries, unless the user accepts an entry as
   pending in writing (then it blocks the order instead).
