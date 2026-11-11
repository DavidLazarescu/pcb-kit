#!/bin/bash
# silkrender.sh BOARD OUT.png [WxH+X+Y]
# Renders F.Mask (pads, orange), F.CrtYd (light blue) and F.SilkS (black) into one PNG.
# Needs kicad-cli, rsvg-convert and ImageMagick (magick). Optional crop in pixels.
# Use gridcrop.py to cut a board-coordinate window with a grid.
set -e
[ $# -ge 2 ] || { sed -n '2,5p' "$0"; exit 1; }
d=$(mktemp -d); trap 'rm -r "$d"' EXIT; b="$1"
for L in F.Mask F.SilkS F.CrtYd; do
  kicad-cli pcb export svg --layers "$L,Edge.Cuts" --mode-single --exclude-drawing-sheet \
    --page-size-mode 2 -o "$d/$L.svg" "$b" >/dev/null 2>&1
  rsvg-convert -z 6 -b white "$d/$L.svg" -o "$d/$L.png"
done
magick "$d/F.Mask.png" -fill '#f0a040' -opaque black "$d/m.png"
magick "$d/F.CrtYd.png" -fill '#a8c8f0' -opaque black -transparent white "$d/c.png"
magick "$d/F.SilkS.png" -transparent white "$d/s.png"
magick "$d/m.png" "$d/c.png" -composite "$d/s.png" -composite ${3:+-crop $3 +repage} "$2"
