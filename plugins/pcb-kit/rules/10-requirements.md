# Phase 10: requirements

- Write requirements as a numbered table: id, requirement, value, status ([F] fixed by the user, [A] assumption, [?] open).
- Ask the kickoff questions before planning: sources/loads and voltages, maximum power and duration, channel count, operating modes, accuracy, interfaces, connectors and current rating, thermal environment, supply budget, isolation, power-on and failure state.
- State the power-on and failure state explicitly (off, zero output, open switch). Every later default-state check traces back to it.
- **A protection signal that nobody drives must mean "protect".** Check every node of a hardware cut-off for the case
  that its driver is missing or its pin is open (assembly fault): the pull resistor goes to the safe level, and nothing
  else on the node (an indicator LED to GND, a divider) may hold it at an undefined level. Drive indicators from their
  own transistor instead of hanging them on the safety node. Open-drain, active-low alarm outputs fail the other way
  (a broken line reads "fine"); cover those with a power-up presence check and a bench test of the whole chain.
- Derive worst-case numbers early: P = V x I at the worst corner decides the thermal design, not the typical point.
- Isolation: decide by ground concept. One island, one ground point. A second galvanic path between two systems creates a ground loop. Non-isolated is acceptable only if the measurement tolerates a few mV offset and the return is current-limited (series resistor or PTC) or all boards share one ground point.
- List open questions with who can answer them. Do not start component selection while a blocking question is open.
