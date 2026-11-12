#!/usr/bin/env bash
# Usage: bom_fpcheck.sh <project_dir | root.kicad_sch | netlist.net> [--parts-dir DIR] [--fp-dir DIR]...
# Gate command: runs fpcheck for every fitted part (one line per MPN) and checks that each footprint
# has an existing 3D model. Statuses: PASS, FAIL, NO-RECORD, MISSING-3D, BOM-ONLY (no footprint, skipped).
# Exit 0 only if every part with a footprint passes.
# DNP parts are skipped. Read-only with respect to the KiCad project.
set -u
here=$(cd "$(dirname "$0")" && pwd)
in=${1:-}; shift || true
[ -n "$in" ] || { echo "usage: $0 <project_dir|root.kicad_sch|netlist.net> [fpcheck options]" >&2; exit 2; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
if [ -d "$in" ]; then pro=$(ls "$in"/*.kicad_pro 2>/dev/null | head -1); sch=${pro%.kicad_pro}.kicad_sch; proj=$in; else sch=$in; proj=$(dirname "$in"); fi
case "$sch" in
  *.net) net=$sch ;;
  *) command -v kicad-cli >/dev/null || { echo "kicad-cli not found" >&2; exit 2; }
     net=$tmp/n.net
     kicad-cli sch export netlist --format kicadsexpr -o "$net" "$sch" >/dev/null 2>&1 || { echo "netlist export failed" >&2; exit 2; } ;;
esac
python3 -I - "$here" "$net" "$proj" "$@" <<'PY'
import subprocess, sys, json, os
here, net, proj, *extra = sys.argv[1:]
sys.path.insert(0, here)
import fplib
comps = fplib.load_netlist(net)
groups = {}
for ref, c in comps.items():
    if c["dnp"]:
        continue
    key = (c["fields"].get("MPN") or c["value"], c["footprint"])
    groups.setdefault(key, []).append(ref)
opts = ["--project-dir", proj, "--fp-dir", proj, "--fp-dir", os.path.join(proj, "libs")] + extra
rows, bad = [], 0
for (mpn, fp), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
    refs.sort()
    if not fp:
        # BOM-only item (no footprint: cable, screw, insulator); nothing to check on the board
        rows.append(("BOM-ONLY", ",".join(refs) if len(refs) < 4 else "%s..(%d)" % (refs[0], len(refs)), mpn, "-", []))
        continue
    r = subprocess.run([sys.executable, os.path.join(here, "fpcheck.py"), mpn, "--netlist", net, "--ref", refs[0], "--json"] + opts,
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except Exception:
        d = dict(status="FAIL", errors=[r.stderr.strip()])
    st, errs = d["status"], d["errors"]
    if st == "NO-RECORD":
        r3 = subprocess.run([sys.executable, os.path.join(here, "fpcheck.py"), fp, "--only-3d", "--json"] + opts, capture_output=True, text=True)
        try:
            d3 = json.loads(r3.stdout)
            if d3["status"] != "PASS":
                errs = errs + d3["errors"]; st = "NO-RECORD+MISSING-3D"
        except Exception:
            pass
    if st != "PASS":
        bad += 1
    rows.append((st, ",".join(refs) if len(refs) < 4 else "%s..(%d)" % (refs[0], len(refs)), mpn, fp.split(":")[-1], errs))
w = max(len(r[1]) for r in rows)
for st, refs, mpn, fp, errs in rows:
    print("%-22s %-*s %-26s %s" % (st, w, refs, mpn[:26], fp[:40]))
    if st not in ("PASS", "NO-RECORD", "BOM-ONLY"):
        for e in errs:
            print("      - " + e)
nb = sum(1 for r in rows if r[0] == "BOM-ONLY")
print("%d of %d parts PASS, %d BOM-only" % (len(rows) - bad - nb, len(rows) - nb, nb))
sys.exit(1 if bad else 0)
PY
