---
name: pcb-requirements
description: Collects and structures PCB requirements before design: kickoff questions, requirements table, ground and isolation concept, power-on state, worst-case power. Use when defining what a board must do or when requirements change.
when_to_use: A board's purpose, limits, loads, interfaces or isolation need to be defined or revised.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/10-requirements.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/10-requirements.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Requirements

## Inputs
User answers from `pcb-new-project`, existing docs, datasheets or specs of what the board connects to.

## Steps
1. Read the rule layers above.
2. Ask what is missing. Group questions; mark who can answer each.
3. Write the requirements table in `DESIGN.md`: id, requirement, value, status [F]/[A]/[?].
4. Compute worst-case numbers: maximum power V x I at the worst corner, supply budget, accuracy targets versus what the other side can resolve.
5. Decide isolation by the ground concept: one island, one ground point. A second galvanic path creates a ground loop; load current through a shared return is not acceptable. A non-isolated board needs a mV-tolerant measurement and a current-limited return.
6. Define the power-on, reset and failure state (off, zero, open). Write it as a requirement.
7. Define hardware protection requirements (overcurrent, overtemperature, SOA, reverse polarity, fuse) and what is hardware-enforced regardless of software.
8. Write driver rules the host software must follow (they later become schematic notes).
9. Log decisions as D# with who and date.

## Gate (done when)
- [ ] Requirements table has no unmarked entry
- [ ] Power-on and failure state stated
- [ ] Worst-case power computed
- [ ] Isolation decision recorded with reason
- [ ] No blocking [?] left

## Outputs
`DESIGN.md` sections: decisions, requirements, facts, open questions.

## Pitfalls
- Typical-point design: size for the worst corner.
- Isolation decided after parts are chosen.
- Questions mixed with assumptions; keep [A] and [?] visible.
