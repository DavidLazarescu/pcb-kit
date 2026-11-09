---
name: pcb-workflow
description: Entry point for designing a PCB in KiCad 10 with the Konnect MCP server. Defines the phases (requirements, components, calculations, schematic spec, schematic build, verification, layout plan, layout, manufacture), the gate between phases, rule layering and project documents. Use when starting or resuming a board design, asking what comes next, or adding a rule.
when_to_use: The user designs, continues, reviews or plans a PCB, or asks where a board design stands.
---

# PCB workflow

Phase skills each add what the generic Konnect skills (`konnect`, `kicad-schematic`, `kicad-library`, `kicad-pcb`, `kicad-review`, `kicad-manufacture`) lack. Invoke `konnect` first for any KiCad work.

## Phases and gates

| # | Phase (skill) | Gate: true before the next phase |
|---|---|---|
| 0 | `pcb-new-project` | Folders, project CLAUDE.md, `pcb-rules/` exist; kickoff questions asked |
| 10 | `pcb-requirements` | Requirements table complete, power-on state defined, no blocking open question |
| 20 | `pcb-components` | Every part: exact MPN, stock + date, datasheet saved, footprint checked, trap list done |
| 30 | `pcb-calculations` | Every block calculated and documented, thermal and SOA done, critical loop simulated across corners |
| 40 | `pcb-schematic-spec` | Spec lists every part, pin and net; reviewed against DESIGN |
| 50 | `pcb-schematic-build` | Sheets built by Konnect, repo committed beforehand, style and review-layout rules met (`rules/45`), system overview created or updated (`rules/41`) |
| 60 | `pcb-verify` | Netlist matches spec, ERC reviewed, BOM fields complete, baseline saved, sheets review-ready, overview current, independent check done |
| 70 | `pcb-layout-plan` | Written routing plan, approved by the user |
| 80 | `pcb-layout` | Routed per plan, DRC 0, independent review done |
| 90 | `pcb-manufacture` | Stock re-checked, outputs generated, first-board bench tests listed |

Do not skip a gate. If a later phase reveals an earlier error, go back, fix the document first, then the design.

## Rule layering

Each phase skill reads, in order, the kit rules (`${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md`, `${CLAUDE_PLUGIN_ROOT}/rules/<phase>.md`) and then the project rules (`pcb-rules/00-house-standards.md`, `pcb-rules/<phase>.md`). Later layers win. Conflicts are stated to the user.

Phase files: 10-requirements, 20-components, 30-calculations-simulation, 40-schematic-spec, 50-schematic-build, 60-verification, 70-layout-plan, 80-layout, 90-manufacture.

## Documents per project

| File | Content |
|---|---|
| `docs/<board>/DESIGN.md` | Decisions D#, requirements, calculations, BOM with stock, status marks, routing plan, resume point |
| `docs/<board>/SCHEMATIC_SPEC.md` | Exact build template |
| `docs/<board>/RESEARCH.md` | Alternatives, prices, removed/kept table (optional) |
| `docs/<board>/ROUTING_PLAN.md` | Layout plan |
| `docs/<board>/calc/`, `sim/`, `verify/`, `datasheets/` | Scripts, simulation, baselines, datasheets |
| `pcb-rules/` | Project overrides per phase |
| `parts-registry.md` | Reusable parts across boards |

Templates are in `${CLAUDE_PLUGIN_ROOT}/templates/`. Status marks: [V] verified with source, [A] assumption, [P] pending, [D] decision with who and date, [R] own calculation.

## Working rules that cut across phases
- Konnect only; commit before any agent rework; ERC 0 proves nothing.
- Plan fully before building; write state so a new chat can resume from files (DESIGN section "where to resume").
- One agent per sheet with fixed reference ranges; mechanical lookups to cheap agents.
- Say what was verified and what was not.

## Agents
`part-researcher` (haiku), `schematic-builder` (sonnet), `schematic-verifier` (sonnet).

## Tools
`${CLAUDE_PLUGIN_ROOT}/tools/`: `verify.sh`, `netcompare.py`, `thermal.py`.

## How to add a rule
- Applies to every board: edit `rules/<phase>.md` in the kit, add a line to `CHANGELOG.md`.
- Applies to one project: add it to `pcb-rules/<phase>.md` there.
- A correction from a review or the bench becomes a rule at once, with the cause in one line.
