#!/usr/bin/env python3
"""silkplace: plan reference designator positions on a board and write a KiCad console script.

  silkplace.py BOARD OUT_SCRIPT [--overrides JSON] [--hide REF ...] [--size 1.0]
               [--small 0.8] [--thickness 0.15] [--extras PY]

The board is loaded with pcbnew in memory and never saved. A reference stays where it is if it
is clear, otherwise a greedy search looks around the part's courtyard. "Clear" means the text
ink box (not GetBoundingBox, which overstates it) misses every pad (+0.15 mm), every footprint
silk graphic (+0.1), every other placed reference (+0.2), keeps 0.5 mm from the board edge,
stays within 1.0 mm of its own courtyard and is nearer to it than to any other courtyard
(margin 0.12). A reference never sits inside any courtyard, its own included, in any pass,
since bodies, heat sinks and connector housings cover silk after assembly. References that fit nowhere at the
normal size are retried at the small size; those still unplaced are hidden.

Overrides JSON: {"REF": [x_mm, y_mm, angle_deg, size_mm]}. They are placed first and their
problems are printed (pad, silk, other reference, not nearest to own part, inside a courtyard).

--extras PY: file whose text is inserted into the generated script before P.Refresh(), for
board text and markings. It runs with `P` (pcbnew), `b` (board) and `F` (ref -> footprint).
"""
import argparse
import json
import math

import pcbnew as P

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("board")
ap.add_argument("out_script")
ap.add_argument("--overrides")
ap.add_argument("--hide", nargs="*", default=[], metavar="REF")
ap.add_argument("--size", type=float, default=1.0)
ap.add_argument("--small", type=float, default=0.8)
ap.add_argument("--thickness", type=float, default=0.15)
ap.add_argument("--extras")
a = ap.parse_args()

HIDE = set(a.hide)
SKIP_CRT = HIDE  # hidden refs do not compete for 'nearest'; their courtyards still count
SIZE, SMALL_SIZE, THICK = a.size, a.small, a.thickness
SMALL_THICK = round(THICK * SMALL_SIZE / SIZE, 3)
mm = P.FromMM
b = P.LoadBoard(a.board)
fps = list(b.GetFootprints())


def box(bb, inf=0.0):
    return [P.ToMM(bb.GetLeft()) - inf, P.ToMM(bb.GetTop()) - inf,
            P.ToMM(bb.GetRight()) + inf, P.ToMM(bb.GetBottom()) + inf]


def hit(p, c):
    return p[0] < c[2] and c[0] < p[2] and p[1] < c[3] and c[1] < p[3]


def grow(q, d):
    return [q[0] - d, q[1] - d, q[2] + d, q[3] + d]


edge = box(b.GetBoardEdgesBoundingBox())
inner = [edge[0] + 0.5, edge[1] + 0.5, edge[2] - 0.5, edge[3] - 0.5]
pads, silk, crt = [], [], {}
for f in fps:
    r = f.GetReference()
    for p in f.Pads():
        pads.append((r, box(p.GetBoundingBox(), 0.15)))
    for g in f.GraphicalItems():
        if g.GetLayer() == P.F_SilkS and g.GetClass() != "PCB_TEXT":
            silk.append((r, box(g.GetBoundingBox(), 0.1)))
    cy = f.GetCourtyard(P.F_CrtYd)
    crt[r] = box(cy.BBox()) if cy.OutlineCount() else box(f.GetBoundingBox(False))


def ink(t):
    return box(t.GetEffectiveTextShape().BBox())


def tbox(t, x, y, ang):
    t.SetPosition(P.VECTOR2I(mm(x), mm(y)))
    t.SetTextAngleDegrees(ang)
    return ink(t)


def bdist(p, c):
    return math.hypot(max(c[0] - p[2], p[0] - c[2], 0), max(c[1] - p[3], p[1] - c[3], 0))


def near(r, bb):
    return bdist(bb, crt[r]) <= 1.0


def own_nearest(r, bb):
    d = bdist(bb, crt[r])
    return all(bdist(bb, q) > d + 0.12 for o, q in crt.items() if o != r and o not in SKIP_CRT)


def clear(r, bb, placed, use_crt):
    if r in crt and not (near(r, bb) and own_nearest(r, bb)):
        return False
    if not (bb[0] >= inner[0] and bb[1] >= inner[1] and bb[2] <= inner[2] and bb[3] <= inner[3]):
        return False
    if any(hit(bb, q) for _, q in pads) or any(hit(bb, q) for _, q in silk):
        return False
    if any(hit(bb, grow(q, .2)) for o, q in placed.items() if o != r):
        return False
    if any(hit(bb, q) for q in crt.values()):
        return False
    return True


FPM = {f.GetReference(): f for f in fps}
for f in fps:
    t = f.Reference()
    t.SetTextSize(P.VECTOR2I(mm(SIZE), mm(SIZE)))
    t.SetTextThickness(mm(THICK))
    t.SetKeepUpright(True)

placed, result = {}, {}
SMALL, OVERRIDE_PROBLEMS = [], []
OV = json.load(open(a.overrides)) if a.overrides else {}
for r, (x, y, ang, sz) in OV.items():
    if r not in FPM:
        OVERRIDE_PROBLEMS.append((r, "no such reference"))
        continue
    t = FPM[r].Reference()
    t.SetTextSize(P.VECTOR2I(mm(sz), mm(sz)))
    t.SetTextThickness(mm(SMALL_THICK if sz < SIZE else THICK))
    bb = tbox(t, x, y, ang)
    probs = []
    if any(hit(bb, q) for _, q in pads):
        probs.append("pad " + ",".join(o for o, q in pads if hit(bb, q)))
    if any(hit(bb, q) for _, q in silk):
        probs.append("silk " + ",".join(o for o, q in silk if hit(bb, q)))
    over = [o for o, q in placed.items() if hit(bb, grow(q, .2))]
    if over:
        probs.append("ref " + ",".join(over))
    if not own_nearest(r, bb):
        probs.append("not nearest")
    inside = [o for o, q in crt.items() if hit(bb, q)]
    if inside:
        probs.append("inside courtyard " + ",".join(inside))
    if probs:
        OVERRIDE_PROBLEMS.append((r, "; ".join(probs)))
    placed[r] = bb
    result[r] = (x, y, ang, True)
    if sz < SIZE:
        SMALL.append(r)

todo = []
for f in fps:
    r = f.GetReference()
    if r in HIDE or r in OV:
        continue
    bb = ink(f.Reference())
    if clear(r, bb, placed, True):
        placed[r] = bb
    else:
        todo.append(f)


def cands(f):
    t = f.Reference()
    c = crt[f.GetReference()]
    cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
    t.SetTextAngleDegrees(0)
    i = ink(t)
    w, h = i[2] - i[0], i[3] - i[1]
    g = 0.3
    out = []
    for d in [0] + [k * s for k in (.5, 1, 1.5, 2, 2.5, 3, 3.5, 4.5, 5.5) for s in (1, -1)]:
        out += [(cx + d, c[1] - g - h / 2, 0), (cx + d, c[3] + g + h / 2, 0),
                (c[0] - g - w / 2, cy + d, 0), (c[2] + g + w / 2, cy + d, 0),
                (c[0] - g - h / 2, cy + d, 90), (c[2] + g + h / 2, cy + d, 90)]
    return [(x, y, ang, math.hypot(x - cx, y - cy) + (0.4 if ang else 0)) for x, y, ang in out]


for use_crt in (True,):
    rest = []

    def n_ok(f):
        return sum(clear(f.GetReference(), tbox(f.Reference(), x, y, ang), placed, use_crt)
                   for x, y, ang, _ in cands(f))
    todo.sort(key=n_ok)
    for f in todo:
        r = f.GetReference()
        best = None
        for x, y, ang, s in sorted(cands(f), key=lambda k: k[3]):
            if clear(r, tbox(f.Reference(), x, y, ang), placed, use_crt):
                best = (x, y, ang)
                break
        if best:
            placed[r] = tbox(f.Reference(), *best)
            result[r] = best + (use_crt,)
        else:
            rest.append(f)
    todo = rest

for f in todo:
    t = f.Reference()
    t.SetTextSize(P.VECTOR2I(mm(SMALL_SIZE), mm(SMALL_SIZE)))
    t.SetTextThickness(mm(SMALL_THICK))
rest = []
for f in todo:
    r = f.GetReference()
    best = None
    for uc in (True,):
        for x, y, ang, s in sorted(cands(f), key=lambda k: k[3]):
            if clear(r, tbox(f.Reference(), x, y, ang), placed, uc):
                best = (x, y, ang)
                break
        if best:
            break
    if best:
        placed[r] = tbox(f.Reference(), *best)
        result[r] = best + (uc,)
        SMALL.append(r)
    else:
        rest.append(f)
unplaced = [f.GetReference() for f in rest]
hidden = sorted(HIDE | set(unplaced))

extras = open(a.extras).read() if a.extras else ""
with open(a.out_script, "w") as o:
    o.write("# Reference placement script, generated by silkplace.py.\n"
            "# 1. In the PCB editor run Tools > Update Footprints from Library first (its dialog can\n"
            "#    reset text positions), then save.\n"
            "# 2. Open Tools > Scripting Console and run: exec(open('<path to this file>').read())\n"
            "# 3. Check the result, then save the board. Run this once; it is one undo-able action.\n")
    o.write("import pcbnew as P\nb = P.GetBoard(); F = {f.GetReference(): f for f in b.GetFootprints()}\n")
    o.write("for f in F.values():\n    t = f.Reference(); t.SetTextSize(P.VECTOR2I(P.FromMM(%g), P.FromMM(%g))); "
            "t.SetTextThickness(P.FromMM(%g)); t.SetKeepUpright(True)\n" % (SIZE, SIZE, THICK))
    o.write("for r in %r:\n    F[r].Reference().SetVisible(False)\n" % hidden)
    o.write("M = {\n")
    for r, (x, y, ang, _) in sorted(result.items()):
        o.write("  %r: (%.2f, %.2f, %d),\n" % (r, x, y, ang))
    o.write("}\nfor r, (x, y, ang) in M.items():\n    t = F[r].Reference(); "
            "t.SetPosition(P.VECTOR2I(P.FromMM(x), P.FromMM(y))); t.SetTextAngleDegrees(ang)\n")
    o.write("for r in %r:\n    t = F[r].Reference(); t.SetTextSize(P.VECTOR2I(P.FromMM(%g), P.FromMM(%g))); "
            "t.SetTextThickness(P.FromMM(%g))\n" % (sorted(SMALL), SMALL_SIZE, SMALL_SIZE, SMALL_THICK))
    if extras:
        o.write("# --- extras ---\n" + extras.rstrip("\n") + "\n# --- end extras ---\n")
    o.write("P.Refresh()\n")

print("kept", len(placed) - len(result), "moved", len(result), "small", sorted(SMALL),
      "hidden", hidden, "unplaced", unplaced)
if unplaced:
    print("HIDDEN, no clear spot even at small size:", unplaced)
for r, p in OVERRIDE_PROBLEMS:
    print("OVERRIDE", r, p)
if not OVERRIDE_PROBLEMS:
    print("override problems: none")
