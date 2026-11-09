# Phase 10: requirements

- Write requirements as a numbered table: id, requirement, value, status ([F] fixed by the user, [A] assumption, [?] open).
- Ask the kickoff questions before planning: sources/loads and voltages, maximum power and duration, channel count, operating modes, accuracy, interfaces, connectors and current rating, thermal environment, supply budget, isolation, power-on and failure state.
- State the power-on and failure state explicitly (off, zero output, open switch). Every later default-state check traces back to it.
- Derive worst-case numbers early: P = V x I at the worst corner decides the thermal design, not the typical point.
- Isolation: decide by ground concept. One island, one ground point. A second galvanic path between two systems creates a ground loop. Non-isolated is acceptable only if the measurement tolerates a few mV offset and the return is current-limited (series resistor or PTC) or all boards share one ground point.
- List open questions with who can answer them. Do not start component selection while a blocking question is open.
