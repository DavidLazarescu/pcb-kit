# Part selection traps

| Trap | What to check |
|---|---|
| DAC power-on reset | Variants with midscale (M) versus zero (Z) default. A midscale default switches a load on at half scale after power-up. Choose the variant whose default is the safe state. |
| Temperature sensors with power-up thresholds | LM75-type parts have fixed overtemperature thresholds at power-up; TMP1075-type parts have different register defaults. Read the defaults table, choose by what protects without software. |
| Supply limits output | A DAC or reference cannot exceed its supply: use that as a hardware cap and compute it. |
| Open-drain / weak outputs into high-impedance nodes | Leakage or residual drive leaves a residual voltage; compute the resulting error or current. |
| Unregulated isolated DC/DC modules | Output rises far above nominal at light load. Add minimum load or a regulator behind it. |
| Heat sink | Rth only from the manufacturer's Rth-versus-length curve at the ordered length. The distributor field can describe a different length. |
| Linear-mode MOSFET | Part specified for linear operation; DC SOA line (Spirito effect); size by power, not current. |
| Variant packages | Same symbol, different footprint. Change the footprint. |
| Packaging suffix | `-TR`, `T`, `/DB` select reel, tape or grade. Order the exact one. |
| Capacitor dielectric and case | A value may not exist in a small case (e.g. 47 nF C0G needs 1206). DC bias derating for X7R. |
| Not for new designs | Check the last-time-buy date; order spares with the main order. |
| Connector current | Small-pitch connectors are rated ~1 A; do not use them for amps. |
| Port supplies | A shared, unfused supply rail needs a fuse or PTC on the daughterboard. |
