#!/usr/bin/env python3
# schstubs.py SHEET...: read-only. Lists pin ends where the attached wire runs across the pin (perpendicular),
# where a junction sits on the pin end, or where the straight stub is shorter than 2.54 mm before a corner/junction.
import sys, re, math

def sexp(s):
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)
    st = [[]]
    for t in tok:
        if t == "(": st.append([])
        elif t == ")": x = st.pop(); st[-1].append(x)
        else: st[-1].append(t[1:-1] if t.startswith('"') else t)
    return st[0][0]

def find(n, key): return [c for c in n if isinstance(c, list) and c and c[0] == key]
def one(n, key):
    r = find(n, key); return r[0] if r else None

R = lambda v: round(v, 2)
for path in sys.argv[1:]:
    root = sexp(open(path).read())
    libs = {}
    for ls in find(one(root, "lib_symbols"), "symbol"):
        pins = []
        def walk(n):
            for c in n:
                if isinstance(c, list):
                    if c[0] == "pin":
                        at = one(c, "at"); ln = float(one(c, "length")[1]); num = one(c, "number")[1]
                        pins.append((float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0, ln, num))
                    else: walk(c)
        walk(ls); libs[ls[1]] = pins
    wires = []
    for w in find(root, "wire"):
        p = one(w, "pts"); a, b = one(p[1:], "xy") and p[1], p[2]
        wires.append(((R(float(a[1])), R(float(a[2]))), (R(float(b[1])), R(float(b[2])))))
    junc = {(R(float(one(j, "at")[1])), R(float(one(j, "at")[2]))) for j in find(root, "junction")}
    def wires_at(pt): return [w for w in wires if w[0] == pt or w[1] == pt]
    def on_mid(pt): return [w for w in wires if pt not in w and min(w[0][0], w[1][0]) <= pt[0] <= max(w[0][0], w[1][0]) and min(w[0][1], w[1][1]) <= pt[1] <= max(w[0][1], w[1][1])]
    for s in find(root, "symbol"):
        lid = one(s, "lib_id")[1]; at = one(s, "at"); X, Y, rot = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0
        mir = one(s, "mirror"); mir = mir[1] if mir else ""
        ref = [p[2] for p in find(s, "property") if p[1] == "Reference"][0]
        for (px, py, pa, ln, num) in libs.get(lid, []):
            # pin end is (px,py) in library coords (y up); direction pa points from the end into the body
            x, y, a = px, -py, -pa  # to sheet coords (y down)
            if mir == "y": x, a = -x, 180 - a
            if mir == "x": y, a = -y, -a
            c, sn = math.cos(math.radians(-rot)), math.sin(math.radians(-rot))
            x, y = x * c - y * sn, x * sn + y * c; a = a - rot
            pt = (R(X + x), R(Y + y))
            away = (round(-math.cos(math.radians(a))), round(-math.sin(math.radians(a))))  # from pin end away from body
            ws = wires_at(pt)
            if not ws and not on_mid(pt):
                continue
            probs = []
            if pt in junc or on_mid(pt): probs.append("junction/T at pin")
            for w in ws:
                o = w[1] if w[0] == pt else w[0]
                d = (o[0] - pt[0], o[1] - pt[1]); L = math.hypot(*d)
                u = (round(d[0] / L), round(d[1] / L))
                if u != away: probs.append("wire across pin")
                elif L < 2.53 and (len(wires_at(o)) > 1 or o in junc or on_mid(o)): probs.append(f"stub {L:.2f}")
            if probs:
                print(f"{path.split('/')[-1]:22} {ref:9} pin {num:3} {pt} away={away}: {', '.join(sorted(set(probs)))}")

    # wire nodes where three or more wire ends meet (or a wire end lands mid-span) without a junction dot
    import collections
    cnt = collections.Counter(p for w in wires for p in w)
    for p, n in cnt.items():
        mid = len(on_mid(p))
        if n + 2 * mid >= 3 and p not in junc:
            print(f"{path.split('/')[-1]:22} node {p}: {n + 2 * mid} wire ends, no junction dot")
