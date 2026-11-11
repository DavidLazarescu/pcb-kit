#!/usr/bin/env python3
"""schcheck: text overlap checker for KiCad 7-10 .kicad_sch files (Python stdlib only).

Usage: schcheck.py SHEET.kicad_sch [SHEET2.kicad_sch ...]
Exit code 0 when no findings, 1 otherwise.

Reports, per sheet and reference, every visible text that overlaps
  - a symbol body (lib graphics: rectangles, polylines, circles, arcs, and pin lines),
  - another visible text (fields, labels, notes),
  - a wire segment.
Texts are estimated boxes (stroke font: advance ~0.95 x size, height = size), so the check is
approximate; it errs a little to the strict side. Hidden fields are ignored. A label's own
anchor wire and the symbol pin wires touching a text's own symbol are not exempt on purpose:
a field sitting on its own pin wire is a defect as well.
"""
import math
import re
import sys

CHAR_W = 0.95     # advance per character, in units of font width
LINE_H = 1.0      # glyph box height, in units of font height
NOTE_LINE_H = 1.5  # line pitch inside multi-line notes
EPS = 0.12        # shrink every box by this before testing, so touching is not overlapping


# ---------------------------------------------------------------- parser
def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif c == "(" or c == ")":
            yield c
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while s[j] != '"':
                if s[j] == "\\":
                    j += 1
                    buf.append({"n": "\n"}.get(s[j], s[j]))
                else:
                    buf.append(s[j])
                j += 1
            yield ("S", "".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and s[j] not in " \t\r\n()":
                j += 1
            yield s[i:j]
            i = j


def parse(text):
    stack = [[]]
    for t in tokenize(text):
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop()
            stack[-1].append(node)
        elif isinstance(t, tuple):
            stack[-1].append(t[1])
        else:
            stack[-1].append(t)
    return stack[0][0]


def kids(node, name):
    return [k for k in node if isinstance(k, list) and k and k[0] == name]


def kid(node, name):
    r = kids(node, name)
    return r[0] if r else None


def num(x):
    return float(x)


# ---------------------------------------------------------------- geometry
def rot_pt(x, y, deg):
    a = math.radians(deg)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


class Box:
    def __init__(self, x0, y0, x1, y1, what, ref=""):
        self.x0, self.y0 = min(x0, x1), min(y0, y1)
        self.x1, self.y1 = max(x0, x1), max(y0, y1)
        self.what, self.ref = what, ref

    def overlaps(self, o):
        e = EPS
        return (self.x0 + e < o.x1 - e and o.x0 + e < self.x1 - e and
                self.y0 + e < o.y1 - e and o.y0 + e < self.y1 - e)

    def hit_seg(self, a, b):
        """Does segment a-b cross the shrunk box?"""
        e = EPS
        x0, y0, x1, y1 = self.x0 + e, self.y0 + e, self.x1 - e, self.y1 - e
        if x0 >= x1 or y0 >= y1:
            return False
        (ax, ay), (bx, by) = a, b
        # Liang-Barsky
        dx, dy = bx - ax, by - ay
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
            if p == 0:
                if q < 0:
                    return False
            else:
                t = q / p
                if p < 0:
                    if t > t1:
                        return False
                    t0 = max(t0, t)
                else:
                    if t < t0:
                        return False
                    t1 = min(t1, t)
        return t0 <= t1


class Poly:
    """A symbol graphic: vertices and whether it is a closed (fillable) outline."""
    def __init__(self, pts, ref):
        self.pts, self.ref = pts, ref
        self.closed = len(pts) >= 4 and abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6

    def inside(self, x, y):
        pts = self.pts
        c = False
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c

    def overlaps(self, box):
        for a, b in zip(self.pts, self.pts[1:]):
            if box.hit_seg(a, b):
                return True
        if self.closed:
            e = EPS
            cx, cy = (box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2
            for x, y in ((cx, cy), (box.x0 + e, box.y0 + e), (box.x1 - e, box.y0 + e),
                         (box.x0 + e, box.y1 - e), (box.x1 - e, box.y1 - e)):
                if self.inside(x, y):
                    return True
        return False


def seg_box(a, b):
    return Box(a[0], a[1], b[0], b[1], "seg")


def arc_points(s, m, e):
    """Sample an arc through three points (start, mid, end)."""
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return [s, m, e]
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(y - uy, x - ux) for x, y in (s, m, e))

    def norm(a, base):
        while a < base:
            a += 2 * math.pi
        return a
    a2n, a3n = norm(a2, a1), norm(a3, a1)
    if a2n > a3n:      # mid not between start and end counter-clockwise: go clockwise
        a2n -= 2 * math.pi
        a3n = a3n - 2 * math.pi
        while a3n > a1:
            a3n -= 2 * math.pi
    pts = []
    for i in range(13):
        a = a1 + (a3n - a1) * i / 12
        pts.append((ux + r * math.cos(a), uy + r * math.sin(a)))
    return pts


# ---------------------------------------------------------------- symbol library
def xy(node, name):
    n = kid(node, name)
    return (num(n[1]), num(n[2]))


def sym_primitives(libsym, unit):
    """Return list of ('box'|'line', ...) in lib coordinates (y up) for a unit, plus pin lines."""
    prims = []
    for sub in kids(libsym, "symbol"):
        m = re.match(r".*_(\d+)_(\d+)$", sub[1])
        u, style = (int(m.group(1)), int(m.group(2))) if m else (0, 1)
        if u not in (0, unit) or style not in (0, 1):
            continue
        for g in sub[2:]:
            if not isinstance(g, list) or not g:
                continue
            if g[0] == "rectangle":
                (x0, y0), (x1, y1) = xy(g, "start"), xy(g, "end")
                prims.append(("poly", [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]))
            elif g[0] == "polyline":
                pts = [(num(p[1]), num(p[2])) for p in kid(g, "pts") if isinstance(p, list) and p[0] == "xy"]
                prims.append(("poly", pts))
            elif g[0] == "circle":
                cx, cy = xy(g, "center")
                r = num(kid(g, "radius")[1])
                prims.append(("poly", [(cx + r * math.cos(t * math.pi / 8), cy + r * math.sin(t * math.pi / 8))
                                       for t in range(17)]))
            elif g[0] == "arc":
                prims.append(("poly", arc_points(xy(g, "start"), xy(g, "mid"), xy(g, "end"))))
            elif g[0] == "pin":
                a = kid(g, "at")
                px, py, ang = num(a[1]), num(a[2]), num(a[3])
                ln = num(kid(g, "length")[1])
                prims.append(("poly", [(px, py), (px + ln * math.cos(math.radians(ang)),
                                                  py + ln * math.sin(math.radians(ang)))]))
    return prims


# ---------------------------------------------------------------- text boxes
def text_size(effects):
    f = kid(effects, "font") if effects else None
    s = kid(f, "size") if f else None
    return (num(s[1]), num(s[2])) if s else (1.27, 1.27)


def is_hidden(effects):
    if not effects:
        return False
    h = kid(effects, "hide")
    if h is not None:
        return len(h) < 2 or h[1] != "no"
    return "hide" in effects


def justify(effects):
    j = kid(effects, "justify") if effects else None
    words = set(j[1:]) if j else set()
    return words


def text_box(txt, x, y, rot, effects, what, ref, multiline_pitch=LINE_H):
    sw, sh = text_size(effects)
    lines = txt.split("\n")
    w = max(len(l) for l in lines) * sw * CHAR_W
    h = sh * LINE_H + (len(lines) - 1) * sh * NOTE_LINE_H
    jw = justify(effects)
    # box before rotation, anchor at (0,0), x to the right, y down
    if "left" in jw:
        bx0, bx1 = 0, w
    elif "right" in jw:
        bx0, bx1 = -w, 0
    else:
        bx0, bx1 = -w / 2, w / 2
    if "top" in jw:
        by0, by1 = 0, h
    elif "bottom" in jw:
        by0, by1 = -h, 0
    else:
        by0, by1 = -h / 2, h / 2
    corners = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]
    out = []
    for cx, cy in corners:
        # text rotation is counter-clockwise on screen: y is down, so negate
        rx, ry = rot_pt(cx, -cy, rot)
        out.append((x + rx, y - ry))
    xs, ys = [p[0] for p in out], [p[1] for p in out]
    return Box(min(xs), min(ys), max(xs), max(ys), what, ref)


def label_box(kind, txt, x, y, rot, effects, ref):
    sw, sh = text_size(effects)
    w = len(txt) * sw * CHAR_W
    if kind == "label":
        # local label: text sits beside the wire end, above it for 0/180, beside for 90/270
        off = 0.3
        if rot == 0:
            return Box(x, y - off - sh, x + w, y - off, "label", ref)
        if rot == 180:
            return Box(x - w, y - off - sh, x, y - off, "label", ref)
        if rot == 90:
            return Box(x - off - sh, y - w, x - off, y, "label", ref)
        return Box(x + off, y, x + off + sh, y + w, "label", ref)
    # global / hierarchical: flag box, pointer length ~ sh, margin ~ sh/2
    L = w + sh * 1.5
    H = sh * 1.6
    if rot == 0:
        return Box(x, y - H / 2, x + L, y + H / 2, "label", ref)
    if rot == 180:
        return Box(x - L, y - H / 2, x, y + H / 2, "label", ref)
    if rot == 90:
        return Box(x - H / 2, y - L, x + H / 2, y, "label", ref)
    return Box(x - H / 2, y, x + H / 2, y + L, "label", ref)


# ---------------------------------------------------------------- sheet analysis
def analyse(path):
    root = parse(open(path, encoding="utf-8").read())
    libs = {s[1]: s for s in kids(kid(root, "lib_symbols") or [], "symbol")}
    bodies, texts, wires = [], [], []
    for w in kids(root, "wire"):
        p = kid(w, "pts")
        pts = [(num(q[1]), num(q[2])) for q in p if isinstance(q, list) and q[0] == "xy"]
        for a, b in zip(pts, pts[1:]):
            wires.append((a, b))
    for s in kids(root, "symbol"):
        lid = kid(s, "lib_id")
        if not lid:
            continue
        lid = lid[1]
        at = kid(s, "at")
        ax, ay, rot = num(at[1]), num(at[2]), num(at[3]) if len(at) > 3 else 0.0
        mir = kid(s, "mirror")
        mir = mir[1] if mir else ""
        u = kid(s, "unit")
        unit = int(u[1]) if u else 1
        props = {p[1]: p for p in kids(s, "property")}
        ref = props["Reference"][2] if "Reference" in props else "?"
        libsym = libs.get(lid)
        if libsym is None:
            for k, v in libs.items():
                if k.split(":")[-1] == lid.split(":")[-1]:
                    libsym = v
        if libsym is not None:
            for kind, pts in sym_primitives(libsym, unit):
                tp = []
                for x, y in pts:
                    if mir == "x":
                        y = -y
                    elif mir == "y":
                        x = -x
                    rx, ry = rot_pt(x, y, rot)
                    tp.append((ax + rx, ay - ry))
                bodies.append(Poly(tp, ref))
        for name, p in props.items():
            if len(p) < 3:
                continue
            eff = kid(p, "effects")
            if is_hidden(eff) or is_hidden(p):
                continue
            val = p[2]
            if not val or val == "~":
                continue
            pat = kid(p, "at")
            # A field angle in the file is relative to the symbol: a field stored at 90 on a symbol
            # rotated 90 reads horizontally. Text is never drawn upside down, so reduce mod 180.
            frot = ((num(pat[3]) if len(pat) > 3 else 0) + rot) % 180
            texts.append(text_box(val, num(pat[1]), num(pat[2]), frot, eff, "field " + name, ref))
    for kind in ("label", "global_label", "hierarchical_label"):
        for l in kids(root, kind):
            pat = kid(l, "at")
            eff = kid(l, "effects")
            k = "label" if kind == "label" else "global"
            texts.append(label_box(k, l[1], num(pat[1]), num(pat[2]), num(pat[3]) if len(pat) > 3 else 0,
                                   eff, l[1]))
    for t in kids(root, "text"):
        pat = kid(t, "at")
        eff = kid(t, "effects")
        texts.append(text_box(t[1], num(pat[1]), num(pat[2]), num(pat[3]) if len(pat) > 3 else 0, eff,
                              "note", t[1][:24].replace("\n", " ")))
    return bodies, texts, wires


def check(path):
    bodies, texts, wires = analyse(path)
    findings = []
    for i, t in enumerate(texts):
        for b in bodies:
            if b.overlaps(t):
                findings.append((t.ref, "%s '%s' overlaps body of %s" % (t.what, "", b.ref), t))
        for j in range(i + 1, len(texts)):
            o = texts[j]
            if t.overlaps(o):
                findings.append((t.ref, "%s overlaps %s of %s" % (t.what, o.what, o.ref), t))
        for a, b in wires:
            if t.hit_seg(a, b):
                findings.append((t.ref, "%s overlaps wire (%.2f,%.2f)-(%.2f,%.2f)" % (t.what, a[0], a[1], b[0], b[1]), t))
    return findings


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    total = 0
    for path in argv[1:]:
        res = check(path)
        print("== %s: %d finding(s)" % (path.split("/")[-1], len(res)))
        for ref, msg, t in sorted(res, key=lambda r: (r[0], r[1])):
            print("  %-10s %s  [text box x %.1f..%.1f y %.1f..%.1f]" % (ref, msg, t.x0, t.x1, t.y0, t.y1))
        total += len(res)
    print("TOTAL %d" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
