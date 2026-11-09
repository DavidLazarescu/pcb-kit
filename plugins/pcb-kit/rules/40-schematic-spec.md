# Phase 40: schematic specification

The spec is the exact build template. Anything not listed is not connected.

- One section per sheet. Per part: reference, part (MPN), symbol (library:name), footprint, fields, and every pin with its net.
- Fixed reference ranges per sheet or channel (power 1-29, control 30-99, channel 1 = 1xx, channel 2 = 2xx, harness = 4xx) so a part's origin is readable from its number.
- Cross-sheet nets: global labels with exact names, listed once in the spec.
- Power nets: power symbols whose Value is the net name (`+5V_ISO`, `GND_ISO`). Name grounds of separate islands differently and state they never connect.
- Name important nets (sense, feedback, high-current, critical analog) so net classes and layout rules can target them.
- Note texts: the exact text of every calculation note per block.
- Style requirements go into the spec: connected drawing, pull-ups on bus wires, feedback loops drawn as loops, decoration frames only if the tool can draw them (Konnect cannot).
- Mark library gaps: parts without a KiCad symbol or footprint, and which stdlib symbol to copy.
- The spec is reviewed against the design document before the build. Run the check as a pin-by-pin diff of critical nets.
