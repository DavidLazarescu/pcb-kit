#!/usr/bin/env python3
"""Compare the connectivity of two KiCad netlists (kicadsexpr format).

    kicad-cli sch export netlist --format kicadsexpr -o new.net <root>.kicad_sch
    netcompare.py baseline.net new.net

Nets are compared as sets of (reference, pin); auto-generated net names are ignored.
Exit code 0 = identical connectivity, 1 = changed, 2 = usage or parse error.
"""
import argparse
import re
import sys


def load(path):
    with open(path) as fh:
        tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', fh.read())

    def parse(i):
        out = []
        while i < len(tok):
            x = tok[i]
            if x == '(':
                sub, i = parse(i + 1)
                out.append(sub)
            elif x == ')':
                return out, i + 1
            else:
                out.append(x.strip('"'))
                i += 1
        return out, i

    root = parse(0)[0][0]

    def find(node, key):
        return [c for c in node if isinstance(c, list) and c and c[0] == key]

    nets = {}
    for net in find(find(root, 'nets')[0], 'net'):
        pins = frozenset((find(n, 'ref')[0][1], find(n, 'pin')[0][1]) for n in find(net, 'node'))
        nets[pins] = find(net, 'name')[0][1]
    return nets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('baseline')
    ap.add_argument('new')
    ap.add_argument('--quiet', action='store_true', help='print only the verdict')
    args = ap.parse_args()
    try:
        a, b = load(args.baseline), load(args.new)
    except (OSError, IndexError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    only_a = [(v, sorted(k)) for k, v in a.items() if k not in b]
    only_b = [(v, sorted(k)) for k, v in b.items() if k not in a]
    if not args.quiet:
        print('nets baseline', len(a), 'new', len(b))
        for v, k in only_a:
            print('only in baseline:', v, k)
        for v, k in only_b:
            print('only in new:', v, k)
    same = not only_a and not only_b
    print('IDENTICAL CONNECTIVITY' if same else 'CONNECTIVITY CHANGED')
    return 0 if same else 1


if __name__ == '__main__':
    sys.exit(main())
