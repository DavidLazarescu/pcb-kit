#!/usr/bin/env python3
"""Projected isolation check across all copper layers.

usage: isocheck.py BOARD.kicad_pcb GAP_MM NET[,NET...] [--footprint REF[,REF...]]

The listed nets (and all pads of the listed footprints) are the port side; every other net is the isolated side.
All copper of each side (pads, tracks, vias, zone fills) on every copper layer is projected onto one plane, and
every spot where isolated copper comes closer than GAP_MM to port copper is listed. Same-layer DRC cannot see an
inner plane reaching under the other side. Read-only; KiCad must not hold the board open with unsaved fills.
"""
import sys
import pcbnew

if len(sys.argv) < 4:
    sys.exit(__doc__)
board, gap, port_nets = sys.argv[1], float(sys.argv[2]), set(sys.argv[3].split(","))
port_fps = set(sys.argv[sys.argv.index("--footprint") + 1].split(",")) if "--footprint" in sys.argv else set()

B = pcbnew.LoadBoard(board)
FM, TM = pcbnew.FromMM, pcbnew.ToMM
layers = [l for l in B.GetEnabledLayers().CuStack()]


def is_port(item):
    if item.GetNetname() in port_nets:
        return True
    fp = item.GetParentFootprint() if hasattr(item, "GetParentFootprint") else None
    return bool(fp and fp.GetReference() in port_fps)


port = pcbnew.SHAPE_POLY_SET()
iso = {l: pcbnew.SHAPE_POLY_SET() for l in layers}


def add(item, layer):
    if item.GetNetCode() <= 0:
        return
    target = port if is_port(item) else iso[layer]
    item.TransformShapeToPolygon(target, layer, 0, FM(0.005), pcbnew.ERROR_INSIDE)


for fp in B.GetFootprints():
    for pad in fp.Pads():
        for l in layers:
            if pad.IsOnLayer(l):
                add(pad, l)
for t in B.GetTracks():
    for l in layers:
        if t.IsOnLayer(l):
            add(t, l)
for z in B.Zones():
    if z.GetIsRuleArea() or z.GetNetCode() <= 0:
        continue
    for l in layers:
        if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):
            (port if z.GetNetname() in port_nets else iso[l]).Append(z.GetFilledPolysList(l))

port.Simplify()
grown = pcbnew.SHAPE_POLY_SET(port)
grown.Inflate(FM(gap) - 1, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.01))
spots = 0
for l in layers:
    s = pcbnew.SHAPE_POLY_SET(iso[l])
    s.Simplify()
    s.BooleanIntersection(grown)
    for i in range(s.OutlineCount()):
        bb = s.Outline(i).BBox()
        print(f"{B.GetLayerName(l)}: isolated copper within {gap} mm of port copper (projected) "
              f"({TM(bb.GetLeft()):.2f},{TM(bb.GetTop()):.2f})-({TM(bb.GetRight()):.2f},{TM(bb.GetBottom()):.2f})")
        spots += 1
print("PASS" if spots == 0 else f"FAIL: {spots} spots")
sys.exit(1 if spots else 0)
