#!/usr/bin/env python3
"""silkcopy: apply a silkplace console script to an in-memory copy of a board and save the copy.

  silkcopy.py BOARD CONSOLE_SCRIPT OUT_BOARD

The original is only read. The project's .kicad_pro and .kicad_dru are copied next to the copy
so kicad-cli DRC uses the project's rules. The copy has no library table, so DRC reports
lib_footprint_issues and lib_footprint_mismatch on it; ignore those.
"""
import os
import shutil
import sys

import pcbnew as P

if len(sys.argv) != 4:
    sys.exit(__doc__)
src_board, script, out = sys.argv[1:4]
b = P.LoadBoard(src_board)
F = {f.GetReference(): f for f in b.GetFootprints()}
code = open(script).read().replace("b = P.GetBoard(); ", "").replace("P.Refresh()", "")
exec(code, {"P": P, "b": b, "F": F})
P.SaveBoard(out, b)
stem_in, stem_out = os.path.splitext(src_board)[0], os.path.splitext(out)[0]
for ext in ("_pro", "_dru"):
    if os.path.exists(stem_in + ".kicad" + ext):
        shutil.copyfile(stem_in + ".kicad" + ext, stem_out + ".kicad" + ext)
print("saved", out)
