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
