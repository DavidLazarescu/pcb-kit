# Parts registry

One YAML file per MPN, `parts/<MPN>.yaml` (characters other than letters, digits and `-_.+` become `_`, so `LM75BD,118` is `LM75BD_118.yaml`). Made once per MPN from the package and pinout pages of the datasheet, reused across projects. `tools/fpcheck.py` compares a footprint and the schematic symbol against it. Only the YAML subset below is supported (maps, lists, `[a, b]`, `{k: v}`, scalars, `#` comments).

| Field | Meaning |
|---|---|
| `mpn`, `manufacturer` | Exact order number and maker |
| `package` | `{name, code, pins}`, for example `VSSOP-10`, `DGS0010A` |
| `datasheet` | `{url, revision, page_land_pattern, page_pinout}` (PDF page numbers) |
| `kicad_footprint` | `lib:name` |
| `footprint_sha256` | Hash of the `.kicad_mod` verified. A different hash means RE-VERIFY (fails closed) |
| `pins`, `pitch_mm`, `body_mm` | Lead count (without exposed pad), pitch, body `[x, y]` |
| `land` | List of pad groups `{numbers, size_mm, <layout>}`. Layout is `dual_row: {row_spacing_mm}` (pin 1 top left, counting down, then up the right row), `in_line: {pitch_mm}` or explicit `centres: [[x, y], ...]` (origin at the pad centroid, KiCad y down). `size_mm: null` skips the size check |
| `exposed_pad` | `{present, pad_number, centre_mm, size_mm, must_connect}` (tab included) |
| `drill_mm` | THT: minimum drill the leads need |
| `pin1`, `pin1_side` | Description, and the machine-checked side of pad 1 against the pad centroid: `{x: neg\|mid\|pos, y: neg\|mid\|pos}` |
| `pin_table` | `{pad: datasheet pin name}` |
| `symbol_pin_names` | Optional `{pad: name}` where the symbol legitimately words a pin differently. Comparison ignores case, `~{}`, spaces, `_` and dash variants |
| `risk` | `{level: high\|normal, reason}` |
| `verified` | `{by, date, layers: [record, second_source, physical]}` |
| `tolerance_mm`, `land_position_tol_mm`, `land_size_tol_mm` | Optional overrides (default 0.05). Use the wider ones only where the datasheet land is an example or a MAX value, and say so in `notes` |
| `no_3d_reason` | Optional: the part needs no 3D model, with the reason |
| `notes` | Anything a reader needs |

Commands:

```
tools/fpcheck.py <MPN> --netlist n.net --ref U1 [--fp-dir DIR] [--tol 0.05] [--json]
tools/fpdiff.py A.kicad_mod B.kicad_mod
tools/bom_fpcheck.sh <project dir | root.kicad_sch | netlist.net>
```

Statuses: `PASS`, `FAIL`, `NO-RECORD`, `MISSING-3D`. Any other status blocks the order. Footprints that need no 3D model (mounting holes) are listed one per line in `<project>/3d-exceptions.txt`.
