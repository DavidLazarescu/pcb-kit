# Phase 20: components

## DigiKey research method
1. Use WebFetch on `digikey.de/de/products/result?keywords=<MPN>` (plain `curl` returns 403).
2. Open the product detail page and verify the exact MPN including the packaging suffix (`-TR`, `T`, `/DB`). Quote that MPN.
3. Summaries mis-attribute stock numbers of substitute parts to the searched part. Trust only the detail page of the exact MPN.
4. Flag marketplace items (third-party stock, different lead time and price). Prefer DigiKey-stocked parts.
5. Record stock and the date. Re-check on the order day: parts flip to 0 between planning and ordering.
6. Check lifecycle: "Not For New Designs" and last-time-buy dates. Plan spares and a fallback.
7. Delegate bulk lookups to the `part-researcher` agent.

## Datasheets
- Save datasheets in the project's `datasheets/`. Some vendor sites block automated download (analog.com, microchip.com, littelfuse.com, xppower.com). Ask the user to download to `~/Downloads` and place them. TI links of the form `https://www.ti.com/lit/ds/symlink/<part>.pdf` usually work.
- Values come from the datasheet, with page or table named. Never from a distributor field.

## Selection traps (check every one)
- Power-on-reset variants: DACs come as midscale (M) or zero (Z) variants. Pick the variant whose default state is the safe state.
- Sensors with power-up thresholds (LM75-type: fixed overtemp limits at power-up) behave differently from TMP1075-type defaults. Read the register defaults table.
- Hardware caps by physics: a DAC's supply limits its output, so a supply rail can cap a quantity in hardware regardless of software.
- Open-drain and weak-pull outputs into high-impedance nodes leave residuals. Compute them.
- Heat sinks: take thermal resistance only from the manufacturer's Rth-versus-length curve, for the length you order. Never from the distributor parametric field.
- Linear-mode MOSFETs: choose a part specified for linear operation and check its DC SOA line. Size by power (V x I), not by current.
- Package variants share a symbol but need a different footprint (same pinout, different package).

## Output
- A BOM table: function, MPN, footprint, stock + date, price, status, source.
- Maintain `parts-registry.md` for parts reused across boards.
- A "removed / kept and why" table for KISS and price review.

## Temperature protection measures the hot part
- An over-temperature failsafe senses the device it protects (MOSFET, regulator), not the board copper near
  its heat sink. A board sensor reads low by an unknown margin and cannot see a mounting fault (missing paste,
  loose screw), where the device overheats while the heat sink stays cool.
- Preferred: a remote-diode sensor (TMP451, NCT72 class) with a hardware THERM output whose power-up limits
  already sit at a safe value, and a 2N3904 glued on the device body as the diode. The same chip reports the
  temperature over I²C, so one part gives readback and a software-free cut-off.
- Place the sensor chip next to the remote diode: the D+/D− path carries microamps and millivolts, while the I²C
  and THERM lines that then take the long way are robust logic signals.
- An open sensor wire does not trip THERM on these parts: the driver checks the OPEN status bit at every step.
