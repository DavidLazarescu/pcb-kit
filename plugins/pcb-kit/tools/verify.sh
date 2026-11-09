#!/usr/bin/env bash
# Usage: verify.sh <root.kicad_sch> [baseline.net] [outdir]
# Exports ERC (JSON), netlist and BOM with kicad-cli, optionally compares to a baseline netlist,
# prints a summary. Read-only with respect to the KiCad project.
set -u
sch=${1:-}; base=${2:-}; out=${3:-verify/out}
[ -n "$sch" ] && [ -f "$sch" ] || { echo "usage: $0 <root.kicad_sch> [baseline.net] [outdir]" >&2; exit 2; }
command -v kicad-cli >/dev/null || { echo "kicad-cli not found" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out"
rc=0

kicad-cli sch erc --format json --severity-all -o "$out/erc.json" "$sch" >/dev/null 2>&1 || true
kicad-cli sch export netlist --format kicadsexpr -o "$out/netlist.net" "$sch" >/dev/null 2>&1 || { echo "netlist export failed" >&2; exit 2; }
kicad-cli sch export bom --fields 'Reference,Value,Footprint,Manufacturer,MPN,Supplier,Supplier Part,Datasheet' \
  --group-by Value,Footprint,MPN -o "$out/bom.csv" "$sch" >/dev/null 2>&1 || echo "bom export failed" >&2

echo "== ERC"
python3 - "$out/erc.json" <<'PY'
import json, sys, collections
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print("no ERC report:", e); sys.exit(0)
c = collections.Counter()
for sheet in d.get("sheets", []):
    for v in sheet.get("violations", []):
        c[(v.get("severity"), v.get("type"))] += 1
if not c:
    print("0 violations (does not prove correctness)")
for (sev, typ), n in sorted(c.items(), key=str):
    print(f"{n:4d}  {sev}  {typ}")
PY

echo "== Netlist"
python3 - "$out/netlist.net" <<'PY'
import re, sys
t = open(sys.argv[1]).read()
print("components:", len(re.findall(r'^\s*\(comp\s*$|\(comp \(ref', t, re.M)), " nets:", len(re.findall(r'^\s*\(net\s*$|\(net \(code', t, re.M)))
names = set(re.findall(r'\(net\s*\(code "?\d+"?\)\s*\(name "([^"]+)"', t))
gnds = sorted(n for n in names if 'GND' in n.upper())
print("ground-like nets:", ", ".join(gnds) if gnds else "none")
PY

echo "== BOM fields"
python3 - "$out/bom.csv" <<'PY'
import csv, sys
try:
    rows = list(csv.DictReader(open(sys.argv[1])))
except Exception as e:
    print("no BOM:", e); sys.exit(0)
need = ["Manufacturer", "MPN", "Supplier", "Supplier Part", "Datasheet", "Footprint"]
bad = 0
for r in rows:
    ref = r.get("Reference", "?")
    if ref.startswith(("#", "H", "TP", "FID")) and not r.get("MPN"):
        continue
    miss = [k for k in need if not (r.get(k) or "").strip()]
    if miss:
        bad += 1
        print(f"{ref}: missing {', '.join(miss)}")
print(f"{len(rows)} BOM lines, {bad} with missing fields")
PY

if [ -n "$base" ]; then
  echo "== Netcompare vs $base"
  python3 "$here/netcompare.py" "$base" "$out/netlist.net" || rc=1
fi
echo "Outputs in $out/"
exit $rc
