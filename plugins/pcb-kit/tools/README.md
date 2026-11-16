# pcb-kit tools

Python 3 stdlib plus the `pcbnew` module that ships with KiCad 10 (`import pcbnew` must work with
`python3`). None of the silk tools writes to a project file.

## Silkscreen reference placement

| Tool | Does |
|---|---|
| `silkplace.py BOARD OUT_SCRIPT [--overrides JSON] [--hide REF ...] [--size 1.0] [--small 0.8] [--thickness 0.15] [--extras PY]` | Plans reference positions on an in-memory copy, prints kept/moved/small/hidden/unplaced and override problems, writes a KiCad scripting-console script |
| `silkcopy.py BOARD SCRIPT OUT_BOARD` | Applies that script to an in-memory copy and saves it, copying the project's `.kicad_pro` and `.kicad_dru` next to it |
| `silkrender.sh BOARD OUT.png` | Renders F.Mask (pads), F.CrtYd and F.SilkS into one PNG (kicad-cli, rsvg-convert, ImageMagick) |
| `gridcrop.py BOARD PNG OUT.png X0 Y0 X1 Y1` | Crops the PNG to a board-mm window with a 1 mm grid, labels every 2 mm; scale and origin come from the Edge.Cuts box |

Overrides JSON: `{"REF": [x_mm, y_mm, angle_deg, size_mm]}`. Overrides are placed first and checked
(pad, silk, other reference, nearest part). `--extras PY` is inserted before `P.Refresh()` in the generated
script, for board text and markings; it sees `P`, `b` and `F` (reference to footprint).

### Loop
1. `silkplace.py board.kicad_pcb console.py --hide ...` (plan).
2. `silkcopy.py board.kicad_pcb console.py scratch/copy.kicad_pcb` (apply to a copy).
3. `kicad-cli pcb drc --refill-zones --format json -o drc.json scratch/copy.kicad_pcb`. Expect no `silk_*`
   findings. `lib_footprint_issues` and `lib_footprint_mismatch` come from the copy losing the library
   table; ignore them.
4. `silkrender.sh scratch/copy.kicad_pcb full.png`, then `gridcrop.py` on the dense regions, and look.
5. Edit the overrides and repeat from 1.
6. Give the owner the console script. In the open PCB editor: Update Footprints from Library, Tools >
   Scripting Console, `exec(open(path).read())`, save. Run it once.

## Schematic checks

| Tool | Does |
|---|---|
| `joints.py BOARD.kicad_pcb` | Read-only, PCB. Lists tracks that enter a pad off-centre or graze its edge, vias joined only by touching a track, one via serving several pads, vias whose tracks lead nowhere, vias joined only by zones (with the zone names, so a stray via between two planes stands apart from a stitching or star-point via), T joints in the middle of a track (info) and corners sharper than 135°. Review every finding; chains that reach the pad centre over several short segments and Kelvin taps are expected leftovers. |
| `capcheck.py BOARD.kicad_pcb [--tier IC=N CAP=N ...] [--pins IC=n,n ...] [--only REF ...] [--json OUT]` | Read-only, PCB, zones filled. For every capacitor, follows the real copper (pads, tracks, T joints, vias, zone fill) from each pad to the IC pin it serves and reports signal-leg length and vias, ground-leg length, vias and plane hops, the loop against the ideal for that pin pair (2 × pin distance + pad pitch, pins closer than 1 mm count as 1 mm), and whether the ground pad faces the IC. Fails per tier (rule 80, *Capacitor placement*); tier 3 is reported only. `--pins` names the real supply and return pins (a shutdown or address pin tied to GND is not a return). The score compares placement variants of one board, lower is better. Exit 0 when nothing fails. |
| `isocheck.py BOARD.kicad_pcb GAP_MM NET[,NET...]` | Read-only, PCB. Projects all copper of the listed port-side nets (pads, tracks, vias, zone fills, every copper layer) against all other copper on every layer and lists every spot closer than GAP_MM. Same-layer DRC misses a plane on an inner layer that reaches under the other side. Empty list and `PASS` is the pass. |
| `schstubs.py SHEET.kicad_sch ...` | Read-only. Lists pins (power symbols, test points, parts) that meet a wire across, sit on a T or have a stub shorter than 2.54 mm, and wire nodes with three or more ends but no junction dot. Run after every schematic edit; empty output is the pass. |
