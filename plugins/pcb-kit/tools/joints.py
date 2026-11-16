#!/usr/bin/env python3
# usage: joints.py BOARD.kicad_pcb
# Joint review for a routed board: off-centre pad entries, tracks grazing pads, vias joined by touch only,
# T joints in the middle of a track, 90 degree / acute corners, two pads sharing one via. Read-only.
import pcbnew, sys, math, collections
B = pcbnew.LoadBoard(sys.argv[1])
TM = pcbnew.ToMM
TOL = 0.02
def P(v): return (TM(v.x), TM(v.y))
def d(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

tracks = [t for t in B.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
vias = [t for t in B.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
pads = [p for f in B.GetFootprints() for p in f.Pads() if p.GetNetCode() > 0]
issues = collections.defaultdict(list)

def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    L = (bx - ax) ** 2 + (by - ay) ** 2
    if L == 0: return d(p, a), 0
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / L))
    return d(p, (ax + t * (bx - ax), ay + t * (by - ay))), t

def pad_hit(pt, layer, netcode):
    for p in pads:
        if p.GetNetCode() == netcode and p.IsOnLayer(layer) and p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(pt[0]), pcbnew.FromMM(pt[1]))):
            return p
    return None

ends = collections.defaultdict(list)   # (layer, net, rounded pt) -> tracks
for t in tracks:
    for e in (P(t.GetStart()), P(t.GetEnd())):
        ends[(t.GetLayer(), t.GetNetCode(), (round(e[0], 2), round(e[1], 2)))].append(t)

for t in tracks:
    L, n = t.GetLayer(), t.GetNetCode(); a, b = P(t.GetStart()), P(t.GetEnd()); w = TM(t.GetWidth())
    name = f"{t.GetNetname()} {B.GetLayerName(L)} ({a[0]:.3f},{a[1]:.3f})->({b[0]:.3f},{b[1]:.3f})"
    for e in (a, b):
        # T in the middle of another track
        for o in tracks:
            if o is t or o.GetLayer() != L or o.GetNetCode() != n: continue
            oa, ob = P(o.GetStart()), P(o.GetEnd())
            if d(e, oa) < TOL or d(e, ob) < TOL: continue
            dist, s = seg_dist(e, oa, ob)
            if dist < TOL and 0 < s < 1:
                issues["T joint in the middle of a track (info)"].append(f"{name} ends on ({oa[0]:.2f},{oa[1]:.2f})->({ob[0]:.2f},{ob[1]:.2f})")
    # track overlapping a same-net pad: fine if it ends at the pad centre or runs through the centre
    for p in pads:
        if p.GetNetCode() != n or not p.IsOnLayer(L): continue
        c = P(p.GetPosition())
        if d(a, c) < TOL or d(b, c) < TOL: continue
        if seg_dist(c, a, b)[0] < 0.05: continue
        poly = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(poly, L, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
        tp = pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(tp, L, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
        x = pcbnew.SHAPE_POLY_SET(tp); x.BooleanIntersection(poly)
        if not x.OutlineCount() or x.Area() < pcbnew.FromMM(1) * pcbnew.FromMM(1) * 0.02: continue
        # entry along a pad axis: one end lies on a line through the centre (x or y) and chains to the centre
        onaxis = [e for e in (a, b) if (abs(e[0] - c[0]) < TOL or abs(e[1] - c[1]) < TOL)
                  and any(d(P(o.GetStart()), c) < TOL or d(P(o.GetEnd()), c) < TOL
                          for o in ends.get((L, n, (round(e[0], 2), round(e[1], 2))), []))]
        if onaxis: continue
        # is this segment part of a chain that reaches the pad centre? (end inside the pad joined to a segment ending at the centre)
        inside = [e for e in (a, b) if p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(e[0]), pcbnew.FromMM(e[1])), pcbnew.FromMM(0.02))]
        chained = any(d(P(o.GetStart()), c) < TOL or d(P(o.GetEnd()), c) < TOL
                      for o in ends.get((L, n, (round(inside[0][0], 2), round(inside[0][1], 2))), []) if o is not t) if inside else False
        if chained: continue
        kind = "ends off-centre inside the pad" if inside else "grazes the pad edge"
        issues[f"track {kind}"].append(f"{name} on {p.GetParentFootprint().GetReference()}.{p.GetNumber()} (centre {seg_dist(c, a, b)[0]:.2f} mm from the track)")
    # other-net via under/near? (DRC covers clearance) - skip

for v in vias:
    c = P(v.GetPosition()); n = v.GetNetCode()
    joined = [t for t in tracks if t.GetNetCode() == n and (d(P(t.GetStart()), c) < TOL or d(P(t.GetEnd()), c) < TOL)]
    touching = []
    for t in tracks:
        if t.GetNetCode() != n or t in joined: continue
        dist, s = seg_dist(c, P(t.GetStart()), P(t.GetEnd()))
        if dist < TM(v.GetWidth(pcbnew.F_Cu)) / 2 + TM(t.GetWidth()) / 2:
            touching.append(t)
    for t in touching:
        issues["via joined by touch, not by a track end"].append(f"via {v.GetNetname()} ({c[0]:.3f},{c[1]:.3f}) / track ({TM(t.GetStart().x):.3f},{TM(t.GetStart().y):.3f})->({TM(t.GetEnd().x):.3f},{TM(t.GetEnd().y):.3f})")
    # one via shared by two pads
    pc = set()
    for t in joined:
        for e in (P(t.GetStart()), P(t.GetEnd())):
            q = pad_hit(e, t.GetLayer(), n)
            if q is not None: pc.add(f"{q.GetParentFootprint().GetReference()}.{q.GetNumber()}")
    if len(pc) > 1:
        issues["one via serves several pads directly"].append(f"via {v.GetNetname()} ({c[0]:.2f},{c[1]:.2f}) -> {sorted(pc)}")

# vias left over after a clean-up: no track and no pad at all, or only tracks that lead to nothing.
# They still join two planes, so DRC and the unconnected list stay quiet; a stitching via that is meant
# to be one is listed too and is fine to leave.
def chain_reaches(v, n, c):
    start = [t for t in tracks if t.GetNetCode() == n and (d(P(t.GetStart()), c) < TOL or d(P(t.GetEnd()), c) < TOL)]
    seen, stack = set(), list(start)
    while stack:
        t = stack.pop()
        if t.m_Uuid.AsString() in seen: continue
        seen.add(t.m_Uuid.AsString())
        for e in (P(t.GetStart()), P(t.GetEnd())):
            if d(e, c) < TOL: continue
            if pad_hit(e, t.GetLayer(), n) is not None: return start, True
            if any(o.GetNetCode() == n and d(P(o.GetPosition()), e) < TM(o.GetWidth(pcbnew.F_Cu)) / 2 + TOL
                   for o in vias if o.m_Uuid.AsString() != v.m_Uuid.AsString()): return start, True
            stack += ends.get((t.GetLayer(), n, (round(e[0], 2), round(e[1], 2))), [])
    return start, False
for v in vias:
    n, c = v.GetNetCode(), P(v.GetPosition())
    if any(p.GetNetCode() == n and p.HitTest(v.GetPosition()) for p in pads): continue
    start, ok = chain_reaches(v, n, c)
    if not start:
        zn = sorted({(z.GetZoneName() or "unnamed") + "/" + B.GetLayerName(l) for z in B.Zones() for l in z.GetLayerSet().Seq()
                     if z.GetNetCode() == n and not z.IsTeardropArea() and not z.GetIsRuleArea() and v.IsOnLayer(l)
                     and z.HitTestFilledArea(l, v.GetPosition(), 0)})
        issues["via joined only by zones: stray, or stitching (read the zones)"].append(
            f"via {v.GetNetname()} ({c[0]:.3f},{c[1]:.3f}) zones {zn}")
    elif not ok:
        issues["via whose tracks lead nowhere"].append(f"via {v.GetNetname()} ({c[0]:.3f},{c[1]:.3f}), {len(start)} dead track(s)")

# corners between exactly two segments without pad/via
for (L, n, pt), ts in ends.items():
    if len(ts) != 2: continue
    if pad_hit(pt, L, n) is not None or any(d(P(v.GetPosition()), pt) < TOL for v in vias if v.GetNetCode() == n): continue
    dirs = []
    for t in ts:
        a, b = P(t.GetStart()), P(t.GetEnd())
        o = b if d(a, pt) < TOL else a
        dirs.append(math.atan2(o[1] - pt[1], o[0] - pt[0]))
    ang = abs(math.degrees(dirs[0] - dirs[1])) % 360
    ang = min(ang, 360 - ang)
    if ang < 134:
        issues[f"corner sharper than 135 deg"].append(f"{ts[0].GetNetname()} {B.GetLayerName(L)} at ({pt[0]:.2f},{pt[1]:.2f}) angle {ang:.0f}")

for k, v in issues.items():
    print(f"== {k}: {len(v)}")
    for s in v[:60]: print("   ", s)
print("joint review done:", sum(len(v) for v in issues.values()), "findings")
