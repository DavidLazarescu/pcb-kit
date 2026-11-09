#!/usr/bin/env python3
"""fpdiff: compare two .kicad_mod footprints (e.g. KiCad stdlib vs a manufacturer, SnapEDA or
Ultra Librarian download). Python 3 stdlib only.

Both footprints are moved to the bbox centre of their pad centres, then 4 rotations x 2 mirrors
of B are tried against A. The best transform is reported; anything except identity is a flag.
Exit 0 only if the transform is identity and no delta exceeds --tol.

  fpdiff.py A.kicad_mod B.kicad_mod [--tol 0.1] [--json]
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fplib  # noqa: E402

# (name, mirror_x, quarter turns); mirror applied first (x -> -x), then rotate counter-clockwise in the
# KiCad frame (y down), which is a clockwise turn on screen.
TRANSFORMS = [("identity", False, 0)] + \
             [("rot%d" % (90 * k), False, k) for k in (1, 2, 3)] + \
             [("mirror-x", True, 0)] + [("mirror-x+rot%d" % (90 * k), True, k) for k in (1, 2, 3)]


def apply(pt, mirror, k):
    x, y = pt
    if mirror:
        x = -x
    for _ in range(k):
        x, y = y, -x
    return x, y


def side_pads(path):
    fp = fplib.load_footprint(path)
    best = {}
    for p in fp["pads"]:
        if p["num"] == "" or p["kind"] == "np_thru_hole":
            continue
        best.setdefault(p["num"], []).append(p)
    return fp, best


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--tol", type=float, default=0.1)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    fa, pa = side_pads(a.a)
    fb, pb = side_pads(a.b)
    flags = []
    common = sorted(set(pa) & set(pb), key=lambda s: (len(s), s))
    if set(pa) - set(pb):
        flags.append("pads only in A: %s" % ",".join(sorted(set(pa) - set(pb))))
    if set(pb) - set(pa):
        flags.append("pads only in B: %s" % ",".join(sorted(set(pb) - set(pa))))
    if len(fa["pads"]) != len(fb["pads"]):
        flags.append("pad count A=%d B=%d" % (len(fa["pads"]), len(fb["pads"])))
    if not common:
        print("FAIL no common pad numbers")
        sys.exit(1)

    def first(d, n):
        return max(d[n], key=lambda p: p["w"] * p["h"])

    ca = fplib.bbox_centre([(first(pa, n)["x"], first(pa, n)["y"]) for n in common])
    cb = fplib.bbox_centre([(first(pb, n)["x"], first(pb, n)["y"]) for n in common])

    best = None
    for name, mir, k in TRANSFORMS:
        cost = 0.0
        for n in common:
            p, q = first(pa, n), first(pb, n)
            tx, ty = apply((q["x"] - cb[0], q["y"] - cb[1]), mir, k)
            cost += math.hypot(tx - (p["x"] - ca[0]), ty - (p["y"] - ca[1]))
        if best is None or cost < best[0] - 1e-9:
            best = (cost, name, mir, k)
    _, tname, mir, k = best
    if tname != "identity":
        flags.append("best transform is %s: B is rotated or mirrored relative to A" % tname)

    rows = []
    for n in common:
        p, q = first(pa, n), first(pb, n)
        tx, ty = apply((q["x"] - cb[0], q["y"] - cb[1]), mir, k)
        dx, dy = tx - (p["x"] - ca[0]), ty - (p["y"] - ca[1])
        qw, qh = (q["h"], q["w"]) if k % 2 else (q["w"], q["h"])
        row = dict(pad=n, dx=round(dx, 3), dy=round(dy, 3), dw=round(qw - p["w"], 3), dh=round(qh - p["h"], 3))
        rows.append(row)
        if max(math.hypot(dx, dy), abs(row["dw"]), abs(row["dh"])) > a.tol:
            flags.append("pad %s differs: centre (%.2f, %.2f), size (%.2f, %.2f)" % (n, dx, dy, row["dw"], row["dh"]))

    def cy(fp, rot):
        pts = fp["courtyard"]
        if not pts:
            return None
        w = max(x for x, _ in pts) - min(x for x, _ in pts)
        h = max(y for _, y in pts) - min(y for _, y in pts)
        return (h, w) if rot else (w, h)

    ya, yb = cy(fa, False), cy(fb, k % 2)
    if ya and yb:
        if max(abs(ya[0] - yb[0]), abs(ya[1] - yb[1])) > a.tol:
            flags.append("courtyard A %.2fx%.2f, B %.2fx%.2f" % (ya + yb))
    else:
        flags.append("courtyard missing in %s" % ("A" if not ya else "B"))

    out = dict(transform=tname, pads=rows, flags=flags, status="PASS" if not flags else "FLAG")
    if a.json:
        print(json.dumps(out))
    else:
        print("%s  transform=%s  pads compared=%d  max centre delta=%.3f mm" % (
            out["status"], tname, len(common), max(math.hypot(r["dx"], r["dy"]) for r in rows)))
        for f in flags:
            print("  - " + f)
    sys.exit(0 if not flags else 1)


if __name__ == "__main__":
    main()
