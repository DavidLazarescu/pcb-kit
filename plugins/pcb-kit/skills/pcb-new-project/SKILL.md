---
name: pcb-new-project
description: Scaffolds a new PCB project from the pcb-kit templates (docs folder, KiCad hardware folder, pcb-rules, project CLAUDE.md, parts registry) and asks the kickoff questions. Use when the user starts a new board, daughterboard or KiCad project.
when_to_use: The user says they want to design a new board or start a new KiCad project.
---

# New PCB project

Invoke `pcb-workflow` for the phase overview and `konnect` before touching KiCad.

## Inputs
Board name (`<board>`), repository root, purpose in one sentence.

## Steps
1. Locate the repo root. Find existing boards and `parts-registry.md` (reuse list).
2. Create:
   - `docs/<board>/` with `DESIGN.md`, `SCHEMATIC_SPEC.md`, `RESEARCH.md`, `ROUTING_PLAN.md` copied from `${CLAUDE_PLUGIN_ROOT}/templates/`, plus `calc/ sim/ verify/ datasheets/`.
   - `Boards/<board>/Hardware/` (leave empty; the KiCad project is created later with Konnect `create_project`).
   - `pcb-rules/` copied from `${CLAUDE_PLUGIN_ROOT}/templates/pcb-rules/`.
   - `parts-registry.md` from the template if none exists.
   - A project `CLAUDE.md` from `templates/project-CLAUDE.md`, filled in. Append to an existing one instead of overwriting.
3. Fill the header of `DESIGN.md` (board, date, status "planning").
4. Ask the kickoff questions, grouped, in one message (see `pcb-requirements`): loads/sources and voltages, power and duration, channels, modes, accuracy, interfaces, connectors and current, thermal environment, supply budget, isolation, power-on and failure state, price target, assembly constraints, deadline.
5. Record answers as [F] in `DESIGN.md` section 1 and requirements. Open ones as [?].
6. Ask whether the house standards need project overrides; write them to `pcb-rules/00-house-standards.md`.
7. Commit the scaffold.

## Gate
Folders and files exist, kickoff questions asked, answers recorded.

## Pitfalls
- Do not create the KiCad project by file copy; use Konnect.
- Do not start selecting parts before blocking questions are answered.
