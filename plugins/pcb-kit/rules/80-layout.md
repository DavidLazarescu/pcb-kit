# Phase 80: layout (to be extended after the first layout)

- Needs KiCad running with the board open in the PCB editor (IPC). Nobody else edits the board meanwhile.
- Follow the written routing plan. Place fixed parts first (connectors, isolating parts), then critical clusters, then the rest, then decoupling at the pins.
- Critical nets by hand first. Then the rest by hand: consistent widths, 45 degree corners, no acute angles, no stubs, aligned buses, few vias, tidy fanout, stitched pours, readable silkscreen.
- Freerouting only as a reviewed draft for non-critical leftovers, never as the result.
- Check each critical net against the plan after routing it.
- Finish with DRC 0 and an independent review by a different agent.
- Commit before each large automated step.
