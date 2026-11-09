#!/usr/bin/env python3
"""fp_requests: turn bom_fpcheck output into the download list for the user.

  bash bom_fpcheck.sh <project> > check.txt ; python3 fp_requests.py check.txt [--generic-ok] > FOOTPRINT_REQUESTS.md

Every part that is not PASS ends up in the list with what is missing (datasheet/record, footprint,
3D model) and where the user should put the download. With --generic-ok, standard chip passives
(R/C/L/fuse 0402…2512 on KiCad stdlib footprints) are listed separately as "covered by a generic
chip record" instead of as downloads.
"""
import re, sys
CHIP = re.compile(r"^(R|C|L|Fuse)_(0402|0603|0805|1206|1210|2010|2512)_\d+Metric$")
rows, cur = [], None
for line in open(sys.argv[1]):
    m = re.match(r"^(PASS|FAIL|NO-RECORD(?:\+MISSING-3D)?|MISSING-3D)\s+(\S+)\s+(\S+)\s+(\S+)", line)
    if m:
        cur = dict(status=m[1], refs=m[2], mpn=m[3], fp=m[4], notes=[]); rows.append(cur)
    elif cur and line.strip().startswith("-"):
        cur["notes"].append(line.strip()[2:])
generic = "--generic-ok" in sys.argv
need, chips = [], []
for r in rows:
    if r["status"] == "PASS" or r["mpn"] == "n/a":
        continue
    if generic and CHIP.match(r["fp"]) and r["status"] == "NO-RECORD":
        chips.append(r); continue
    want = []
    if "NO-RECORD" in r["status"]:
        want.append("datasheet (package + pinout pages)")
    if "MISSING-3D" in r["status"]:
        want.append("3D model (STEP)")
    if r["status"] == "FAIL":
        want.append("check: " + "; ".join(r["notes"][:3]))
    need.append((r, want))
print("# Footprint requests\n")
print("Put downloads into `libs/downloads/<MPN>/` (zip from the manufacturer, SnapEDA or Ultra Librarian,")
print("or the datasheet PDF). Claude then imports, checks against the datasheet and reports ACCEPTED or REJECTED.\n")
print("| Refs | MPN | Footprint now | Needed |\n|---|---|---|---|")
for r, want in need:
    print(f"| {r['refs']} | {r['mpn']} | `{r['fp']}` | {', '.join(want)} |")
if chips:
    print("\nCovered by generic chip records (no download): " + ", ".join(f"{r['refs']} ({r['fp']})" for r in chips))
