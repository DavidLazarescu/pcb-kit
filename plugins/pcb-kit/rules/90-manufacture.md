# Phase 90: manufacture

- Run the stock check again on the order day for every MPN (parts flip to 0 stock). Check Not-For-New-Designs and last-time-buy dates; order spares with the main order.
- BOM fields complete; DNP flags set for variants.
- Footprints verified per `25-footprint-verification.md`: `tools/bom_fpcheck.sh` all PASS and L3 sign-off done. The order is blocked otherwise.
- DRC 0, independent layout review done, silkscreen labels for connectors and indicators, board name, version and date.
- Fab outputs (gerbers, drill, position file, BOM) via the `kicad-manufacture` skill. Match the fab house's rules (min track, clearance, via) to the project config.
- Keep the verified schematic baseline and the release outputs in the repo.
- List first-board bench tests (from the simulation results) in the design document.
