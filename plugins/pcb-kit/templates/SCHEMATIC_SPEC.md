# <board> schematic specification (v1)

Build spec. Rationale and calculations: `DESIGN.md`. Every connection below is intended; anything not listed is not connected.

## 0. Project, conventions
- Project: `Boards/<board>/Hardware/<board>.kicad_pro`.
- Hierarchy: root sheet plus sheets `<sheet>.kicad_sch` "<title>". A4 landscape, signal flow left to right, supplies top, grounds bottom.
- Cross-sheet nets as global labels with exactly these names: `<NET1> <NET2>`.
- Power nets (power symbols, Value = net name): `<+5V ...>`, grounds `<GND>`, `<GND_ISO>` (never connected to each other).
- Fields on every part: Value, Footprint, Manufacturer, MPN, Supplier = Digikey, Supplier Part = MPN, Datasheet.
- Footprints: passives `Resistor_SMD:R_0603_1608Metric`, `Capacitor_SMD:C_0603_1608Metric`, others from the KiCad stdlib.
- Reference ranges: sheet A 1-29, sheet B 30-99, channel 1 = 1xx, channel 2 = 2xx, harness = 4xx.
- Style: connected drawing, labels only between blocks, pull-ups on bus wires, feedback loops drawn as loops, stdlib symbols copied.

### Parts used repeatedly
| Item | MPN | Footprint |
|---|---|---|

## 1. Root sheet
- Sheet symbols, mounting holes, overview text (purpose, decisions, pinouts, address table, driver rules).

## 2. Sheet `<name>`
| Ref | Part (MPN) | Symbol | Footprint | Connections (pin: net) |
|---|---|---|---|---|

Notes (exact text, with calculations):
- "<note>"

## 3. Library gaps
| Part | Missing | Copy from |
|---|---|---|
