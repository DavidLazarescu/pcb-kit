# Thermal and SOA

- Steady state: Tj = Ta + P (Rjc + Rcs + Rsa). Allowed P = (Tjmax_design - Ta) / (Rjc + Rcs + Rsa). Use a design Tj well below the absolute maximum (for example 110 C).
- Rcs: use the interface material value (paste, insulating pad) from the datasheet; add the insulator. When unsure, take the worse value.
- Rsa: manufacturer's Rth-versus-length curve at the ordered length and the mounting orientation. A distributor field can describe another length (a 1.25 K/W listing was about 2.1 K/W at 50 mm and about 1.05 K/W at 100 mm).
- Transient: sink capacitance C = mass x specific heat (aluminium 0.897 J/gK), tau = Rsa x C. Single shot: time until limit = -tau ln(1 - allowed/P_over). Heat-sink mass is often not published; state the assumption.
- Back-to-back tests: iterate on / off cycles with exponential heating and cooling; report the cycle at which the sink reaches the start limit and the cut-off limit.
- Cut-off: when a hardware temperature cut-off acts at a sink temperature Tsink, the junction is Tsink + P x path; check it stays below the limit.
- Linear-mode MOSFET: DC SOA line at the case temperature reached; the pulsed SOA curves do not apply to seconds-long loads. Spirito effect: at high VDS and low current the device can become thermally unstable; a part specified for linear mode has the SOA line extended there. Check the operating point (V, I) lies under the DC line with margin.
- Size by power V x I at the worst corner, not by current.
