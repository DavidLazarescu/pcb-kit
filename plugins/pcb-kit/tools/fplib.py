"""Shared helpers for fpcheck.py and fpdiff.py. Python 3 stdlib only.

- sexpr(): KiCad S-expression parser
- load_footprint(): .kicad_mod -> pads, courtyard
- load_netlist(): kicadsexpr netlist -> components, pin names
- load_yaml(): parser for the YAML subset used by parts/*.yaml (see parts/README.md)
"""
import hashlib
import math
import re


# ---------------------------------------------------------------- S-expressions
def sexpr(text):
    toks = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+', text)
    pos = 0

    def parse():
        nonlocal pos
        if toks[pos] != "(":
            t = toks[pos]
            pos += 1
            if t.startswith('"'):
                return ("s", re.sub(r"\\(.)", r"\1", t[1:-1]))
            return t
        pos += 1
        out = []
        while toks[pos] != ")":
            out.append(parse())
            # parse() returns tuple for strings; keep as plain str inside lists
        pos += 1
        return out

    def flat(n):
        if isinstance(n, tuple):
            return n[1]
        if isinstance(n, list):
            return [flat(c) for c in n]
        return n

    return flat(parse())


def children(node, tag):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == tag]


def child(node, tag):
    r = children(node, tag)
    return r[0] if r else None


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------- footprints
def load_footprint(path):
    root = sexpr(open(path, encoding="utf-8").read())
    pads = []
    for p in children(root, "pad"):
        at = child(p, "at")
        size = child(p, "size")
        rot = float(at[3]) if len(at) > 3 else 0.0
        w, h = float(size[1]), float(size[2])
        if round(rot) % 180 == 90:
            w, h = h, w
        drill = None
        d = child(p, "drill")
        if d:
            nums = [float(x) for x in d[1:] if re.fullmatch(r"-?[\d.]+", x)]
            drill = min(nums) if nums else None
        layers = child(p, "layers") or []
        pads.append(dict(num=p[1], kind=p[2], shape=p[3], x=float(at[1]), y=float(at[2]),
                         w=w, h=h, drill=drill, layers=layers[1:]))
    crt = []
    for tag in ("fp_line", "fp_rect", "fp_circle", "fp_poly", "fp_arc"):
        for e in children(root, tag):
            lay = child(e, "layer")
            if not lay or lay[1] != "F.CrtYd":
                continue
            for key in ("start", "end", "center", "mid"):
                c = child(e, key)
                if c:
                    crt.append((float(c[1]), float(c[2])))
            pts = child(e, "pts")
            if pts:
                for xy in children(pts, "xy"):
                    crt.append((float(xy[1]), float(xy[2])))
    models = [m[1] for m in children(root, "model")]
    return dict(name=root[1], pads=pads, courtyard=crt, models=models)


def resolve_model(path, project_dir=None):
    """Expand KiCad path variables in a (model ...) path; return the existing file or None."""
    base = "/usr/share/kicad/3dmodels"
    for var in re.findall(r"\$\{(\w+)\}", path):
        if var == "KIPRJMOD":
            val = project_dir or "."
        elif var.endswith("3DMODEL_DIR") or var == "KISYS3DMOD":
            val = base
        else:
            val = __import__("os").environ.get(var, "")
        path = path.replace("${%s}" % var, val)
    import os
    return path if os.path.isfile(path) else None


def numbered(pads):
    """One pad per pad number (largest copper area wins; paste/thermal-via copies share a number)."""
    best = {}
    for p in pads:
        if p["num"] == "" or p["kind"] == "np_thru_hole":
            continue
        if p["num"] not in best or p["w"] * p["h"] > best[p["num"]]["w"] * best[p["num"]]["h"]:
            best[p["num"]] = p
    return best


def bbox_centre(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


# ---------------------------------------------------------------- netlist
def _is_dnp(c):
    val = (child(c, "value") or [0, ""])[1]
    if val.upper().startswith("DNP") or child(c, "dnp") or child(c, "exclude_from_bom"):
        return True
    for f in children(child(c, "fields") or ["fields"], "field"):
        if child(f, "name")[1] in ("Fitted", "DNP") and len(f) > 2 and f[2].upper().startswith("DNP"):
            return True
    return False


def load_netlist(path):
    root = sexpr(open(path, encoding="utf-8").read())
    comps = {}
    for c in children(child(root, "components"), "comp"):
        ref = child(c, "ref")[1]
        fields = {}
        for f in children(child(c, "fields") or ["fields"], "field"):
            fields[child(f, "name")[1]] = f[2] if len(f) > 2 else ""
        ls = child(c, "libsource")
        comps[ref] = dict(ref=ref, value=(child(c, "value") or [0, ""])[1],
                          footprint=(child(c, "footprint") or [0, ""])[1], fields=fields,
                          lib=ls and child(ls, "lib")[1], part=ls and child(ls, "part")[1],
                          dnp=_is_dnp(c), pinnames={})
    libpins = {}
    lp = child(root, "libparts")
    for part in (children(lp, "libpart") if lp else []):
        d = {}
        for pin in children(child(part, "pins") or ["pins"], "pin"):
            d[child(pin, "num")[1]] = child(pin, "name")[1]
        libpins[(child(part, "lib")[1], child(part, "part")[1])] = d
    for c in comps.values():
        c["pinnames"] = dict(libpins.get((c["lib"], c["part"]), {}))
    for net in children(child(root, "nets"), "net"):
        for node in children(net, "node"):
            pf = child(node, "pinfunction")
            ref = child(node, "ref")[1]
            pin = child(node, "pin")[1]
            if pf and ref in comps and pin not in comps[ref]["pinnames"]:
                comps[ref]["pinnames"][pin] = pf[1]
    return comps


def norm_pin(s):
    s = str(s).lower().replace("~{", "").replace("}", "")
    s = re.sub(r"[\u2010-\u2015\u2212]", "-", s)
    return re.sub(r"[\s_]+", "", s)


def strip_pin_suffix(name, num):
    """The netlist writes unnamed or duplicate pin functions as <name>_<pad>."""
    return name[: -len(num) - 1] if name.endswith("_" + num) else name


# ---------------------------------------------------------------- YAML subset
def _strip_comment(line):
    q = None
    for i, ch in enumerate(line):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _split_key(text):
    q = None
    depth = 0
    for i, ch in enumerate(text):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == ":" and depth == 0 and (i + 1 == len(text) or text[i + 1] == " "):
            return text[:i].strip(), text[i + 1:].strip()
    return None


def _scalar(s):
    s = s.strip()
    if s[:1] in "\"'" and s[-1:] == s[:1] and len(s) >= 2:
        return s[1:-1]
    if s.startswith("[") or s.startswith("{"):
        v, _ = _flow(s, 0)
        return v
    if s in ("~", "null", ""):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?", s):
        return float(s)
    return s


def _flow(s, i):
    while s[i] == " ":
        i += 1
    if s[i] == "[":
        out = []
        i += 1
        while True:
            while s[i] in " ,":
                i += 1
            if s[i] == "]":
                return out, i + 1
            v, i = _flow(s, i)
            out.append(v)
    if s[i] == "{":
        out = {}
        i += 1
        while True:
            while s[i] in " ,":
                i += 1
            if s[i] == "}":
                return out, i + 1
            j = i
            q = None
            while not (s[j] == ":" and not q):
                if s[j] in "\"'":
                    q = None if q == s[j] else (q or s[j])
                j += 1
            k = s[i:j].strip().strip("\"'")
            v, i = _flow(s, j + 1)
            out[k] = v
    j = i
    if s[i] in "\"'":
        q = s[i]
        j = s.index(q, i + 1) + 1
        return s[i + 1:j - 1], j
    while s[j] not in ",]}":
        j += 1
    return _scalar(s[i:j]), j


def load_yaml(path):
    lines = []
    for raw in open(path, encoding="utf-8").read().splitlines():
        t = _strip_comment(raw).rstrip()
        if t.strip() and t.strip() != "---":
            lines.append([len(t) - len(t.lstrip(" ")), t.strip()])
    node, i = _node(lines, 0, lines[0][0])
    return node


def _node(lines, i, indent):
    if lines[i][1] == "-" or lines[i][1].startswith("- "):
        return _seq(lines, i, indent)
    return _map(lines, i, indent)


def _seq(lines, i, indent):
    out = []
    while i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
        rest = lines[i][1][1:].strip()
        if rest == "":
            i += 1
            v, i = _node(lines, i, lines[i][0])
        elif _split_key(rest) and rest[0] not in "[{\"'":
            off = lines[i][1].index(rest)
            lines[i] = [indent + off, rest]
            v, i = _node(lines, i, indent + off)
        else:
            v = _scalar(rest)
            i += 1
        out.append(v)
    return out, i


def _map(lines, i, indent):
    out = {}
    while i < len(lines) and lines[i][0] == indent:
        kv = _split_key(lines[i][1])
        if not kv:
            raise ValueError("YAML subset: cannot parse line %r" % lines[i][1])
        k, v = kv
        k = k.strip("\"'")
        i += 1
        if v == "":
            if i < len(lines) and (lines[i][0] > indent or
                                   (lines[i][0] == indent and lines[i][1].startswith("- "))):
                out[k], i = _node(lines, i, lines[i][0])
            else:
                out[k] = None
        else:
            out[k] = _scalar(v)
    return out, i
