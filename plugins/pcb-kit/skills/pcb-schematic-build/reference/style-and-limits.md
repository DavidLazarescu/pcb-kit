# Style and Konnect limits

Style
- Wires within a block; labels only between blocks and sheets; at most one label per net per block.
- Pull-ups on the bus wires themselves; decoupling at the IC pin; dividers inline; feedback loops drawn as loops (output, sense, divider, input, compensation visible).
- Signal flow left to right, supplies at the top, grounds at the bottom.
- Name important nets so net classes and layout rules can target them.
- Calculation notes as text next to the block.
- Copy stdlib symbols; do not draw custom symbols.

Konnect limits
- No title-block tool: the user sets it (File > Page Settings > apply to all sheets).
- No rectangle tool: do not frame with wires.
- `add_power_symbol` cannot name the net: place `power:+5V` / `power:GND`, set Value to the net name (`+5V_ISO`). Verify with kicad-cli that GND and isolated ground stay separate.
- Duplicate `#PWR` references across sheets produce annotation warnings; renumber.
- Dangling stubs from loop drawing: ERC reports them, close them.
- The overlap tool reports power symbols at their own pin; ignore.
- Schematic tools refuse when the sheet is open in the editor; PCB tools need the board open.
- Konnect updates via KiCad PCM change the binary path; after an update re-check the MCP registration and run `konnect init`.
- Linux is not per-platform QA'd: verify results more than usual.
