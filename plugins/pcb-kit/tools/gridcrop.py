#!/usr/bin/env python3
"""gridcrop: crop a silkrender.sh PNG to a board-coordinate window and overlay a millimetre grid.

  gridcrop.py BOARD PNG OUT.png X0 Y0 X1 Y1

Coordinates are board mm. Scale and origin come from the board: the Edge.Cuts bounding box
fills the uncropped PNG (silkrender.sh exports with page size mode 2), so
scale = PNG width / box width. Grid lines every 1 mm, labels every 2 mm.
"""
import subprocess
import sys

import pcbnew as P

if len(sys.argv) != 8:
    sys.exit(__doc__)
board, png, out = sys.argv[1:4]
x0, y0, x1, y1 = map(float, sys.argv[4:8])
bb = P.LoadBoard(board).GetBoardEdgesBoundingBox()
ox, oy = P.ToMM(bb.GetLeft()), P.ToMM(bb.GetTop())
w_px = int(subprocess.check_output(["magick", "identify", "-format", "%w", png]))
k = w_px / P.ToMM(bb.GetWidth())


def px(X):
    return (X - ox) * k


def py(Y):
    return (Y - oy) * k


def line(c, x_a, y_a, x_b, y_b):
    return ["-stroke", c, "-strokewidth", "1", "-draw", "line %d,%d %d,%d" % (x_a, y_a, x_b, y_b)]


def label(x, y, s):
    return ["-stroke", "none", "-fill", "#007070", "-pointsize", "16", "-draw", 'text %d,%d "%d"' % (x, y, s)]


draw = []
X = int(x0)
while X <= x1:
    even = X % 2 == 0
    draw += line("#00a0a0" if even else "#c0e0e0", px(X), py(y0), px(X), py(y1))
    if even:
        draw += label(px(X) + 2, py(y0) + 16, X)
    X += 1
Y = int(y0)
while Y <= y1:
    even = Y % 2 == 0
    draw += line("#00a0a0" if even else "#c0e0e0", px(x0), py(Y), px(x1), py(Y))
    if even:
        draw += label(px(x0) + 2, py(Y) - 2, Y)
    Y += 1
subprocess.run(["magick", png, *draw, "-crop",
                "%dx%d+%d+%d" % (px(x1) - px(x0), py(y1) - py(y0), px(x0), py(y0)),
                "+repage", out], check=True)
