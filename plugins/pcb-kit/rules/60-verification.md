# Phase 60: verification

ERC 0 does not prove correctness. Verify connectivity independently with kicad-cli.

- Netlist: `kicad-cli sch export netlist --format kicadsexpr -o new.net <root>.kicad_sch`.
- Compare against the saved baseline with `tools/netcompare.py`. Expect `IDENTICAL CONNECTIVITY` after cosmetic changes. After intended changes, expect exactly the intended differences and nothing else.
- ERC: `kicad-cli sch erc --format json`. Read violations by type; fix or justify each.
- BOM: `kicad-cli sch export bom` with fields. Every part has Manufacturer, MPN, Supplier, Supplier Part, Datasheet.
- Check critical pins by hand against the spec: isolation barrier pins, supplies of every IC, enable and reset pins, default-state pins, ground islands.
- Island check: no net contains both GND and an isolated ground.
- Render sheets to PDF/SVG and look at them (text overlaps, dangling wires, unreadable notes).
- Save a verified baseline netlist into `verify/` in the repo after each accepted state.
- Verification is done by a different agent than the builder (`schematic-verifier`).
- Say what was verified and what was not.
