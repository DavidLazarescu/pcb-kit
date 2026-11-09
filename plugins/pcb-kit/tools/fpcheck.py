#!/usr/bin/env python3
"""fpcheck: verify a KiCad footprint (and optionally the symbol pin names) against a part record.

Python 3 stdlib only. Exit 0 only if everything passes; a missing record, an unreadable
footprint or a changed footprint hash is a failure (fail closed).

  fpcheck.py INA226 --netlist load.net --ref U204 [--fp-dir DIR] [--tol 0.05] [--json]
  fpcheck.py parts/INA226.yaml --fp some.kicad_mod
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fplib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PARTS = os.path.join(HERE, "..", "parts")
KICAD_FP = "/usr/share/kicad/footprints"


def find_record(parts_dir, mpn):
    if os.path.isfile(mpn):
        return mpn
    safe = "".join(c if c.isalnum() or c in "-_.+" else "_" for c in mpn)
    p = os.path.join(parts_dir, safe + ".yaml")
    return p if os.path.isfile(p) else None


def find_fp(libname, fp_dirs):
    lib, _, name = libname.partition(":")
    for d in fp_dirs + [KICAD_FP]:
        for cand in (os.path.join(d, lib + ".pretty", name + ".kicad_mod"),
                     os.path.join(d, name + ".kicad_mod")):
            if os.path.isfile(cand):
                return cand
    return None


def expected_pads(rec):
    """record land groups -> {pad number: (x, y, w, h)}; pin 1 top-left, KiCad y axis down."""
    out = []
    pitch = float(rec["pitch_mm"])
    for g in rec["land"]:
        nums = [str(n) for n in g["numbers"]]
        w, h = g.get("size_mm") or (None, None)
        if "centres" in g:
            cs = g["centres"]
        elif "dual_row" in g:
            n = len(nums)
            half = n // 2
            rs = float(g["dual_row"]["row_spacing_mm"])
            cs = [[-rs / 2, (i - (half - 1) / 2) * pitch] for i in range(half)]
            cs += [[rs / 2, ((half - 1) / 2 - i) * pitch] for i in range(n - half)]
        elif "in_line" in g:
            p = float(g["in_line"]["pitch_mm"])
            cs = [[i * p, 0.0] for i in range(len(nums))]
        else:
            raise ValueError("land group needs centres, dual_row or in_line")
        if len(cs) != len(nums):
            raise ValueError("land group: %d numbers but %d centres" % (len(nums), len(cs)))
        for n, c in zip(nums, cs):
            out.append((n, float(c[0]), float(c[1]), None if w is None else float(w), None if h is None else float(h)))
    ep = rec.get("exposed_pad") or {}
    if ep.get("present"):
        cen = ep.get("centre_mm", [0, 0])
        out.append((str(ep["pad_number"]), float(cen[0]), float(cen[1]),
                    float(ep["size_mm"][0]), float(ep["size_mm"][1]), "ep"))
    return out


def side(v, eps):
    return "mid" if abs(v) <= eps else ("neg" if v < 0 else "pos")


def model_status(fp_path, project_dir):
    """Exceptions (e.g. mounting holes) are explicit: footprint names in <project>/3d-exceptions.txt."""
    try:
        exc = [l.split("#")[0].strip() for l in open(os.path.join(project_dir, "3d-exceptions.txt"))]
    except OSError:
        exc = []
    if os.path.basename(fp_path)[:-len(".kicad_mod")] in exc:
        return []
    models = fplib.load_footprint(fp_path)["models"]
    if not models:
        return ["no 3D model referenced by the footprint"]
    return ["3D model file not found: %s" % m for m in models if not fplib.resolve_model(m, project_dir)]


def check(rec, fp_path, tol, comp=None):
    errs = []
    fp = fplib.load_footprint(fp_path)
    tol = float(rec.get("tolerance_mm", tol))
    postol = float(rec.get("land_position_tol_mm", tol))
    sztol = float(rec.get("land_size_tol_mm", tol))

    sha = fplib.sha256_file(fp_path)
    if sha != rec.get("footprint_sha256"):
        errs.append("RE-VERIFY footprint hash changed (%s...)" % sha[:12])

    allpads = [p for p in fp["pads"] if p["num"] != "" and p["kind"] != "np_thru_hole"]
    exp = expected_pads(rec)
    ep = rec.get("exposed_pad") or {}
    ep_num = str(ep["pad_number"]) if ep.get("present") else None

    leads = [e for e in exp if len(e) == 5]
    if int(rec["pins"]) != len(set(e[0] for e in leads)):
        errs.append("record inconsistent: pins=%s but land lists %d" % (rec["pins"], len(leads)))
    fnums = set(p["num"] for p in allpads)
    enums = set(e[0] for e in exp)
    if enums - fnums:
        errs.append("pads missing in footprint: %s" % ",".join(sorted(enums - fnums, key=lambda s: (len(s), s))))
    if fnums - enums:
        errs.append("extra pads in footprint: %s" % ",".join(sorted(fnums - enums, key=lambda s: (len(s), s))))

    # Pair each expected pad with the footprint pad of that number that fits best.
    # Pad 1 gives the shift between the two coordinate frames (bbox centre of the paired pads).
    pairs = []
    for e in exp:
        cands = [p for p in allpads if p["num"] == e[0]]
        if not cands:
            continue
        pairs.append((e, min(cands, key=lambda p: 0 if e[3] is None else abs(p["w"] - e[3]) + abs(p["h"] - e[4]))))
    if pairs:
        fc = fplib.bbox_centre([(p["x"], p["y"]) for _, p in pairs])
        ec = fplib.bbox_centre([(e[1], e[2]) for e, _ in pairs])
        for e, p in pairs:
            n = e[0]
            dx = (p["x"] - fc[0]) - (e[1] - ec[0])
            dy = (p["y"] - fc[1]) - (e[2] - ec[1])
            tag = "exposed pad" if len(e) == 6 else "pad"
            if math.hypot(dx, dy) > postol:
                errs.append("%s %s position off by (%.2f, %.2f) mm" % (tag, n, dx, dy))
            if e[3] is not None and (abs(p["w"] - e[3]) > sztol or abs(p["h"] - e[4]) > sztol):
                errs.append("%s %s size %.2fx%.2f, record %.2fx%.2f" % (tag, n, p["w"], p["h"], e[3], e[4]))

        # pitch: the smallest lead spacing is an integer multiple of the record pitch
        lp = [p for e, p in pairs if len(e) == 5]
        pitch = float(rec["pitch_mm"])
        if len(lp) > 1:
            m = min(math.hypot(a["x"] - b["x"], a["y"] - b["y"])
                    for i, a in enumerate(lp) for b in lp[i + 1:])
            k = m / pitch
            if round(k) < 1 or abs(k - round(k)) * pitch > tol:
                errs.append("smallest pad spacing %.3f mm is not a multiple of pitch %s" % (m, pitch))

        p1 = rec.get("pin1_side")
        p1pad = [p for e, p in pairs if e[0] == "1" and len(e) == 5]
        if not isinstance(p1, dict):
            errs.append("record needs pin1_side: {x: neg|mid|pos, y: neg|mid|pos}")
        elif p1pad:
            got = (side(p1pad[0]["x"] - fc[0], tol), side(p1pad[0]["y"] - fc[1], tol))
            want = (p1.get("x", "mid"), p1.get("y", "mid"))
            if got != want:
                errs.append("pin 1 at x:%s y:%s, record expects x:%s y:%s (%s)" % (
                    got[0], got[1], want[0], want[1], (rec.get("pin1") or {}).get("description", "")))

    if ep.get("present") and ep_num not in fnums:
        errs.append("exposed pad %s missing" % ep_num)

    if rec.get("drill_mm") is not None:
        need = float(rec["drill_mm"])
        for p in allpads:
            if p["kind"] == "thru_hole" and (p["drill"] is None or p["drill"] + 1e-9 < need):
                errs.append("pad %s drill %s mm < record %s mm" % (p["num"], p["drill"], need))

    if comp is not None:
        if comp["footprint"] != rec["kicad_footprint"]:
            errs.append("schematic footprint %s != record %s" % (comp["footprint"], rec["kicad_footprint"]))
        names = dict(rec.get("pin_table") or {})
        names = {str(k): v for k, v in names.items()}
        names.update({str(k): v for k, v in (rec.get("symbol_pin_names") or {}).items()})
        for n in sorted(set(e[0] for e in leads), key=lambda s: (len(s), s)):
            want = names.get(n)
            got = comp["pinnames"].get(n)
            if want is None:
                errs.append("record has no pin name for pad %s" % n)
            elif got is None:
                errs.append("symbol has no pin %s (record: %s)" % (n, want))
            elif fplib.norm_pin(fplib.strip_pin_suffix(got, n)) != fplib.norm_pin(want):
                errs.append("pad %s: symbol pin '%s', record '%s'" % (n, got, want))
        for n in comp["pinnames"]:
            if n not in names:
                errs.append("symbol pin %s ('%s') has no pad in the record" % (n, comp["pinnames"][n]))
    return errs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part", help="MPN (looked up in the parts registry) or path to a record")
    ap.add_argument("--parts-dir", default=DEFAULT_PARTS)
    ap.add_argument("--fp", help="footprint file; default: resolved from the record or netlist")
    ap.add_argument("--fp-dir", action="append", default=[], help="project footprint library root (contains X.pretty)")
    ap.add_argument("--netlist")
    ap.add_argument("--ref")
    ap.add_argument("--tol", type=float, default=0.05)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--project-dir", default=".", help="resolves ${KIPRJMOD} in 3D model paths")
    ap.add_argument("--only-3d", action="store_true", help="only check that the footprint's 3D model file exists")
    ap.add_argument("--no-3d-exception", action="store_true")
    a = ap.parse_args()

    ref = a.ref or "-"
    result = dict(ref=ref, mpn=a.part, status="FAIL", errors=[])

    def done(status, errs):
        result.update(status=status, errors=errs)
        if a.json:
            print(json.dumps(result))
        elif status == "PASS":
            print("PASS %s %s" % (ref, a.part))
        else:
            print("%s %s %s" % (status, ref, a.part))
            for e in errs:
                print("  - " + e)
        sys.exit(0 if status == "PASS" else 1)

    if a.only_3d:
        fpfile = a.fp or find_fp(a.part, a.fp_dir)
        if not fpfile:
            done("FAIL", ["footprint file not found for %s" % a.part])
        m = model_status(fpfile, a.project_dir)
        done("PASS" if not m else "MISSING-3D", m)

    path = find_record(a.parts_dir, a.part)
    if not path:
        done("NO-RECORD", ["no record parts/%s.yaml" % a.part])
    try:
        rec = fplib.load_yaml(path)
        comp = None
        if a.netlist:
            comps = fplib.load_netlist(a.netlist)
            if a.ref not in comps:
                done("FAIL", ["reference %s not in netlist" % a.ref])
            comp = comps[a.ref]
        fpfile = a.fp or find_fp(comp["footprint"] if comp and comp["footprint"] else rec["kicad_footprint"], a.fp_dir)
        if not fpfile:
            done("FAIL", ["footprint file not found for %s" % (comp["footprint"] if comp else rec["kicad_footprint"])])
        errs = check(rec, fpfile, a.tol, comp)
        m = [] if rec.get("no_3d_reason") else model_status(fpfile, a.project_dir)
        done("FAIL" if errs else ("MISSING-3D" if m else "PASS"), errs + m)
    except SystemExit:
        raise
    except Exception as e:  # fail closed
        done("FAIL", ["checker error: %s: %s" % (type(e).__name__, e)])


if __name__ == "__main__":
    main()
