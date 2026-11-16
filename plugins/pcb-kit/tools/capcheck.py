#!/usr/bin/env python3
# usage: capcheck.py BOARD [--tier REF=N ...] [--pins IC=N,N ...] [--pair CAP:IC ...] [--only REF ...] [--json OUT]
#
# Checks every capacitor against the IC pins it serves, along the copper that really connects them.
# Read-only. Zones must be filled (plane hops are taken from the fill).
#
# Per capacitor (two pads, reference C*):
#   ic        the nearest U* footprint with pins on both capacitor nets (--pair CAP:IC overrides)
#   sig leg   shortest copper path from the non-ground pad to the IC pin: length, vias
#   gnd leg   shortest copper path from the ground pad to an IC ground pin: length, vias, plane hops, and how
#             far the first via sits from the capacitor pad and the last via from the IC pin
#             (a flying capacitor has two signal legs and no ground leg)
#   loop      both legs plus the capacitor body (mm); area: shoelace over the path points, layers projected
#   gnd_faces the ground pad is the pad nearer to the IC ground pin (checked when supply and ground pin are
#             neighbours, FACE_PIN_DIST)
# Tiers (--tier U105=1 for every capacitor of that IC, or C113=1 for one):
#   1  switching, charge-pump and hot loops (flying, input and output capacitors of converters)
#   2  supply pins of ICs, references, ADC/DAC, amplifier and sensor supplies (default)
#   3  bulk and entry capacitors: reported, never failed
# Limits per tier are in LIMITS. The score (sum of tier-weighted loop length plus a via penalty) compares
# placement variants of one board: lower is better.
import pcbnew, sys, math, heapq, collections, json, argparse

ap = argparse.ArgumentParser()
ap.add_argument("board")
ap.add_argument("--tier", nargs="*", default=[], help="IC=TIER, e.g. U105=1")
ap.add_argument("--pair", nargs="*", default=[], help="CAP:IC, e.g. C113:U105")
ap.add_argument("--only", nargs="*", default=[], help="only these capacitors or ICs")
ap.add_argument("--pins", nargs="*", default=[], help="IC=PINS: the supply and ground pins a capacitor may serve, e.g. U105=2 or U201=1,4 (a shutdown, address or mode pin tied to a rail is not a supply or return)")
ap.add_argument("--json")
a = ap.parse_args()

# loop is a factor on the ideal loop of that pin pair: 2 x (pin-to-pin distance) + capacitor pad pitch, the loop of a
# capacitor sitting right across the two pins. It scales with the package, so an IC whose supply and ground pins are
# on opposite sides is not held to the loop of one whose pins are neighbours.
# gnd_via_dist: capacitor ground pad to its plane via. ic_via_dist: IC ground pin to the via where the return comes up;
# looser, because the IC pin may reach the plane through the ground pad and via of its own capacitor (one via per pad).
LIMITS = {  # vias on the signal legs, via distances (mm), loop factor
    1: dict(sig_vias=0, gnd_via_dist=1.0, ic_via_dist=2.0, loop=2.0),
    2: dict(sig_vias=0, gnd_via_dist=1.2, ic_via_dist=3.0, loop=2.5),
}
WEIGHT = {1: 4.0, 2: 1.0, 3: 0.1}
VIA_MM = 1.0    # score penalty per via in the loop, as equivalent mm of track
MIN_PIN_DIST = 1.0    # mm: a capacitor cannot sit across fine-pitch pins (courtyards), so closer pins count as 1 mm
FACE_PIN_DIST = 2.0   # mm between the IC supply and ground pin up to which the ground pad must face the IC
GND_NAMES = {"GND", "GNDA", "GNDD", "AGND", "DGND", "PGND", "0V", "VSS"}

B = pcbnew.LoadBoard(a.board)
B.BuildConnectivity()
TM, FM = pcbnew.ToMM, pcbnew.FromMM
def P(v): return (TM(v.x), TM(v.y))
def dist(p, q): return math.hypot(p[0] - q[0], p[1] - q[1])
def V(p): return pcbnew.VECTOR2I(FM(p[0]), FM(p[1]))
def is_gnd(net): return net.upper() in GND_NAMES or net.upper().startswith("GND")
COPPER = [l for l in B.GetEnabledLayers().CuStack()]

tiers = {k: int(v) for k, v in (t.split("=") for t in a.tier)}
only_pins = {k: set(v.split(",")) for k, v in (t.split("=") for t in a.pins)}
pairs = dict(p.split(":") for p in a.pair)
fps = {f.GetReference(): f for f in B.GetFootprints()}
ics = [f for r, f in fps.items() if r.startswith("U")]

# ---------- copper graph per net ----------
# nodes: ("pad", ref, num, layer) / ("pt", layer, x, y) / ("via", x, y) / ("zone", uuid)
# a pad is one node per copper layer it is on; vias join all layers they span; zones are a node each
graph = collections.defaultdict(lambda: collections.defaultdict(list))   # net -> node -> [(node, w, kind)]
pos = {}
def edge(net, u, v, w, kind):
    graph[net][u].append((v, w, kind)); graph[net][v].append((u, w, kind))

pads_by_net = collections.defaultdict(list)
for f in B.GetFootprints():
    for p in f.Pads():
        if p.GetNetCode() > 0:
            pads_by_net[p.GetNetname()].append(p)
def pad_node(p, l): return ("pad", p.GetParentFootprint().GetReference(), p.GetNumber(), l)
def pad_layers(p): return [l for l in COPPER if p.IsOnLayer(l)]

for net, ps in pads_by_net.items():
    for p in ps:
        ls = pad_layers(p)
        for l in ls: pos[pad_node(p, l)] = P(p.GetPosition())
        for l in ls[1:]: edge(net, pad_node(p, ls[0]), pad_node(p, l), 0.0, "tht")

def attach(net, node, pt, layer):
    """join a track end or via to the pads on that layer it lands in"""
    for p in pads_by_net[net]:
        if p.IsOnLayer(layer) and p.HitTest(V(pt)):
            edge(net, node, pad_node(p, layer), dist(pt, P(p.GetPosition())), "pad")

tracks = [t for t in B.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
vias = [t for t in B.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
ends = collections.defaultdict(list)
for t in tracks:
    net, l = t.GetNetname(), t.GetLayer()
    s, e = P(t.GetStart()), P(t.GetEnd())
    ns, ne = ("pt", l, round(s[0], 3), round(s[1], 3)), ("pt", l, round(e[0], 3), round(e[1], 3))
    pos[ns], pos[ne] = s, e
    edge(net, ns, ne, dist(s, e), "track")
    ends[(net, l)].append((ns, s, TM(t.GetWidth()) / 2))
    ends[(net, l)].append((ne, e, TM(t.GetWidth()) / 2))
    attach(net, ns, s, l); attach(net, ne, e, l)
# T joints: an end landing on the middle of another track of the same net and layer
for t in tracks:
    net, l = t.GetNetname(), t.GetLayer()
    s, e = P(t.GetStart()), P(t.GetEnd())
    for node, pt, _ in ends[(net, l)]:
        L = dist(s, e)
        if L == 0: continue
        u = ((pt[0] - s[0]) * (e[0] - s[0]) + (pt[1] - s[1]) * (e[1] - s[1])) / L ** 2
        if 0 < u < 1:
            q = (s[0] + u * (e[0] - s[0]), s[1] + u * (e[1] - s[1]))
            if dist(q, pt) < 0.02:
                edge(net, node, ("pt", l, round(s[0], 3), round(s[1], 3)), u * L, "track")
                edge(net, node, ("pt", l, round(e[0], 3), round(e[1], 3)), (1 - u) * L, "track")
# a track running through a pad (not ending in it) joins it at the closest point
for t in tracks:
    net, l = t.GetNetname(), t.GetLayer()
    s, e = P(t.GetStart()), P(t.GetEnd()); L = dist(s, e)
    if L == 0: continue
    for p in pads_by_net[net]:
        if not p.IsOnLayer(l): continue
        c = P(p.GetPosition())
        u = max(0.0, min(1.0, ((c[0] - s[0]) * (e[0] - s[0]) + (c[1] - s[1]) * (e[1] - s[1])) / L ** 2))
        q = (s[0] + u * (e[0] - s[0]), s[1] + u * (e[1] - s[1]))
        if 0 < u < 1 and p.HitTest(V(q)):
            pn = pad_node(p, l)
            edge(net, pn, ("pt", l, round(s[0], 3), round(s[1], 3)), u * L + dist(q, c), "track")
            edge(net, pn, ("pt", l, round(e[0], 3), round(e[1], 3)), (1 - u) * L + dist(q, c), "track")
for v in vias:
    net, c = v.GetNetname(), P(v.GetPosition())
    vn = ("via", round(c[0], 3), round(c[1], 3)); pos[vn] = c
    r = TM(v.GetWidth(pcbnew.F_Cu)) / 2
    for l in COPPER:
        if not v.IsOnLayer(l): continue
        ln = ("vl", l, round(c[0], 3), round(c[1], 3)); pos[ln] = c
        edge(net, vn, ln, 0.0, "via")
        for node, pt, hw in ends[(net, l)]:
            if dist(pt, c) <= r + hw: edge(net, ln, node, dist(pt, c), "track")
        attach(net, ln, c, l)

# zones: every pad or via layer node inside the fill joins the zone node. Crossing a plane costs the
# straight distance (the return runs under the outgoing path, so straight is the honest estimate).
for z in B.Zones():
    if z.GetIsRuleArea() or z.GetNetCode() <= 0 or z.IsTeardropArea(): continue
    net = z.GetNetname()
    for l in COPPER:
        if not z.IsOnLayer(l): continue
        members = []
        for p in pads_by_net[net]:
            if p.IsOnLayer(l) and z.HitTestFilledArea(l, p.GetPosition(), 0):
                members.append((pad_node(p, l), P(p.GetPosition())))
        for v in vias:
            if v.GetNetname() == net and v.IsOnLayer(l) and z.HitTestFilledArea(l, v.GetPosition(), 0):
                c = P(v.GetPosition()); members.append((("vl", l, round(c[0], 3), round(c[1], 3)), c))
        for i, (n1, p1) in enumerate(members):
            for n2, p2 in members[i + 1:]:
                edge(net, n1, n2, dist(p1, p2), "plane")

def shortest(net, srcs, dsts):
    """Dijkstra from any src node to any dst node; returns (length, path nodes, edge kinds)."""
    g = graph[net]; best = {}; prev = {}
    h = [(0.0, s, None, None) for s in srcs]
    while h:
        d0, u, pu, k = heapq.heappop(h)
        if u in best: continue
        best[u] = d0; prev[u] = (pu, k)
        if u in dsts:
            path, kinds = [u], []
            while prev[path[-1]][0] is not None:
                kinds.append(prev[path[-1]][1]); path.append(prev[path[-1]][0])
            return d0, path[::-1], kinds[::-1]
        for v, w, kind in g[u]:
            if v not in best: heapq.heappush(h, (d0 + w, v, u, kind))
    return None

def pad_nodes(p): return {pad_node(p, l) for l in pad_layers(p)}
def count_vias(path): return sum(1 for n in path if n[0] == "via")

def shoelace(pts):
    s = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]): s += x1 * y2 - x2 * y1
    return abs(s) / 2

def via_dists(cpad_pos, ic_pos, path):
    vs = [pos[n] for n in path if n[0] == "via"]
    if not vs: return None, None
    return dist(cpad_pos, vs[0]), dist(ic_pos, vs[-1])

def ic_pins(ic, net):
    ps = [p for p in ic.Pads() if p.GetNetname() == net]
    keep = [p for p in ps if p.GetNumber() in only_pins.get(ic.GetReference(), ())]
    return keep or ps

rows = []
for ref, f in sorted(fps.items(), key=lambda kv: (kv[0][0], int("".join(c for c in kv[0] if c.isdigit()) or 0))):
    if not ref.startswith("C") or len(f.Pads()) != 2: continue
    pa, pb = f.Pads()
    if pa.GetNetCode() <= 0 or pb.GetNetCode() <= 0: continue
    if all(is_gnd(p.GetNetname()) for p in (pa, pb)): continue
    if ref in pairs:
        ic = fps[pairs[ref]]
    else:
        cands = [(min(dist(P(q.GetPosition()), P(f.GetPosition())) for p in (pa, pb) for q in ic_pins(ic, p.GetNetname())), ic)
                 for ic in ics if all(ic_pins(ic, p.GetNetname()) for p in (pa, pb))]
        if not cands: continue
        ic = min(cands, key=lambda c: c[0])[1]
    if a.only and ref not in a.only and ic.GetReference() not in a.only: continue
    tier = tiers.get(ref, tiers.get(ic.GetReference(), 2))
    legs = {}
    for cp in (pa, pb):
        targets = ic_pins(ic, cp.GetNetname())
        r = shortest(cp.GetNetname(), pad_nodes(cp), set().union(*(pad_nodes(q) for q in targets)))
        if r is None: break
        L, path, kinds = r
        vd = via_dists(P(cp.GetPosition()), pos[path[-1]], path)
        legs[cp.GetNumber()] = dict(pad=cp, gnd=is_gnd(cp.GetNetname()), len=L, vias=count_vias(path),
                                    planes=kinds.count("plane"), vd=vd, path=path)
    if len(legs) < 2:
        rows.append(dict(cap=ref, ic=ic.GetReference(), tier=tier, error="no copper path")); continue
    la, lb = legs[pa.GetNumber()], legs[pb.GetNumber()]
    pts = [pos[n] for n in la["path"][::-1]] + [pos[n] for n in lb["path"]]
    pts = [p for i, p in enumerate(pts) if i == 0 or dist(p, pts[i - 1]) > 1e-6]
    area = shoelace(pts) if len(pts) >= 3 else 0.0
    loop = la["len"] + lb["len"] + dist(P(pa.GetPosition()), P(pb.GetPosition()))
    ideal = 2 * max(MIN_PIN_DIST, dist(pos[la["path"][-1]], pos[lb["path"][-1]])) + dist(P(pa.GetPosition()), P(pb.GetPosition()))
    sig = [l for l in (la, lb) if not l["gnd"]]
    gl = [l for l in (la, lb) if l["gnd"]]
    gfaces = None
    # orientation only counts where the IC's supply and ground pins are neighbours; across a package the
    # datasheet layouts put the ground via at the capacitor instead
    if gl and dist(pos[sig[0]["path"][-1]], pos[gl[0]["path"][-1]]) <= FACE_PIN_DIST:
        g, s_ = gl[0]["pad"], sig[0]["pad"]
        gp = ic_pins(ic, g.GetNetname())
        gfaces = min(dist(P(g.GetPosition()), P(q.GetPosition())) for q in gp) <= \
                 min(dist(P(s_.GetPosition()), P(q.GetPosition())) for q in gp) + 0.05
    why = []
    if tier in LIMITS:
        lim = LIMITS[tier]
        for l in sig:
            if l["vias"] > lim["sig_vias"]: why.append(f"vias on {l['pad'].GetNetname().split('/')[-1]} leg")
        for l in gl:
            if l["vias"]:
                d1, d2 = l["vd"]
                if d1 > lim["gnd_via_dist"]: why.append(f"gnd via {d1:.1f}mm from cap pad")
                if d2 > lim["ic_via_dist"]: why.append(f"gnd via {d2:.1f}mm from IC pin")
        if loop > lim["loop"] * ideal: why.append(f"loop {loop:.1f}>{lim['loop']}x{ideal:.1f}mm")
        if gfaces is False and gl[0]["vias"]: why.append("gnd pad faces away")   # a direct top-copper return is judged by the loop
        if f.GetLayer() != ic.GetLayer(): why.append("other side")
    rows.append(dict(cap=ref, ic=ic.GetReference(), tier=tier, value=f.GetValue(),
                     nets="/".join(p.GetNetname().split("/")[-1] for p in (pa, pb)),
                     sig_mm=round(sum(l["len"] for l in sig), 2), sig_vias=sum(l["vias"] for l in sig),
                     gnd_mm=round(gl[0]["len"], 2) if gl else None, gnd_vias=gl[0]["vias"] if gl else 0,
                     plane_hops=la["planes"] + lb["planes"], loop_mm=round(loop, 2), ideal_mm=round(ideal, 2), area_mm2=round(area, 2),
                     vias=la["vias"] + lb["vias"], gnd_faces=gfaces, ok=not why, why=", ".join(why)))

def row_score(r): return WEIGHT[r["tier"]] * (r["loop_mm"] + VIA_MM * r["vias"])
score = sum(row_score(r) for r in rows if "error" not in r)
print(f"{'cap':6}{'ic':6}{'t':>2} {'value':10}{'nets':20}{'sig':>5}{'sv':>3}{'gnd':>6}{'gv':>3}{'pl':>3}{'loop':>6}{'ideal':>6}{'area':>6} gnd  result")
for r in sorted(rows, key=lambda r: (r["tier"], r["ic"], r["cap"])):
    if "error" in r:
        print(f"{r['cap']:6}{r['ic']:6}{r['tier']:>2}  {r['error']}"); continue
    gf = {True: "ok  ", False: "AWAY", None: "-   "}[r["gnd_faces"]]
    g = f"{r['gnd_mm']:6.1f}" if r["gnd_mm"] is not None else "     -"
    res = "info" if r["tier"] not in LIMITS else ("PASS" if r["ok"] else "FAIL " + r["why"])
    print(f"{r['cap']:6}{r['ic']:6}{r['tier']:>2} {r['value'][:9]:10}{r['nets'][:19]:20}{r['sig_mm']:5.1f}{r['sig_vias']:3}"
          f"{g}{r['gnd_vias']:3}{r['plane_hops']:3}{r['loop_mm']:6.1f}{r['ideal_mm']:6.1f}{r['area_mm2']:6.1f} {gf} {res}")
fails = sum(1 for r in rows if "error" in r or (r["tier"] in LIMITS and not r["ok"]))
print(f"\n{len(rows)} capacitors, {fails} fail, score {score:.1f} (lower is better; compare variants of one board)")
if a.json: json.dump(dict(rows=rows, score=score), open(a.json, "w"), indent=1)
sys.exit(1 if fails else 0)
