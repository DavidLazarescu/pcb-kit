# pcb-kit

A Claude Code plugin: knowledge base and workflow for designing PCBs in KiCad 10 with the Konnect MCP server. It distils two real projects (an electronic load and a cell-voltage emulator) into rules, phase skills with gates, agents, templates and verification tools.

It adds to, and does not replace, the generic Konnect skills (`konnect`, `kicad-schematic`, `kicad-library`, `kicad-pcb`, `kicad-review`, `kicad-manufacture`). Phase skills tell you to invoke `konnect` first.

## Contents

| Part | What |
|---|---|
| `skills/pcb-workflow` | Entry point: phases, gates, rule layering, documents |
| `skills/pcb-new-project` ... `pcb-manufacture` | One skill per phase |
| `rules/` | Kit rules: house standards plus one file per phase |
| `agents/` | `part-researcher` (haiku), `schematic-builder`, `schematic-verifier` (sonnet) |
| `templates/` | DESIGN, SCHEMATIC_SPEC, ROUTING_PLAN, RESEARCH, project CLAUDE.md, `pcb-rules/`, parts registry |
| `tools/` | `verify.sh`, `netcompare.py`, `thermal.py` |
| `hooks/` | Blocks text edits of `*.kicad_*` files |

Phases: 10 requirements, 20 components, 30 calculations and simulation, 40 schematic spec, 50 schematic build, 60 verification, 70 layout plan, 80 layout, 90 manufacture. Layout skills are thin and get extended after the first layout.

## Install

```
/plugin marketplace add DavidLazarescu/pcb-kit
/plugin install pcb-kit@pcb-kit
```

Or in `~/.claude/settings.json` (or the project's `.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "pcb-kit": { "source": { "source": "github", "repo": "DavidLazarescu/pcb-kit" } }
  },
  "enabledPlugins": { "pcb-kit@pcb-kit": true }
}
```

Local checkout instead of GitHub: `/plugin marketplace add /path/to/pcb-kit`.

Requirements: KiCad 10 with `kicad-cli`, the Konnect MCP server registered in Claude Code, `python3`, optionally ngspice.

## Update

```
/plugin marketplace update pcb-kit
/plugin update pcb-kit@pcb-kit
```

Bump `version` in `plugins/pcb-kit/.claude-plugin/plugin.json` and add a line to `CHANGELOG.md` with every change, or clients will not see the update.

## Rule layering

Every phase skill reads, in order: kit `rules/00-house-standards.md`, kit `rules/<phase>.md`, project `pcb-rules/00-house-standards.md`, project `pcb-rules/<phase>.md`. Later wins. Conflicts are stated to the user. The project root is the nearest folder with `pcb-rules/`, else the git root. `pcb-new-project` copies `templates/pcb-rules/` into a new project.

## How to use

Start a board with `pcb-new-project`, then follow `pcb-workflow`. Resume by reading the project's `docs/<board>/DESIGN.md`, section "Status / where to resume".

## How to add a rule

1. Decide scope. Applies to every board: edit `plugins/pcb-kit/rules/<phase>.md` (or `00-house-standards.md`). Applies to one project: edit that project's `pcb-rules/<phase>.md`.
2. Write it as one imperative line, with the reason if it is not obvious. Put detail in a skill's `reference/` file.
3. If a skill's steps or gate change too, edit that `SKILL.md`.
4. Add a line to `CHANGELOG.md`, bump the plugin version, commit.
5. A correction from a review or the bench becomes a rule the same day.

## Hook limits

`block-kicad-text-edits.sh` blocks Edit, Write and NotebookEdit on `*.kicad_sch|pcb|pro|sym|mod` and the library tables, and, best effort, Bash commands that combine such a file name with `sed -i`, `perl -i`, `tee`, redirection, `cp`, `mv`, `rm`. It does not detect indirection (variables, generated scripts, a Python script writing the file). Konnect remains the only supported way to change KiCad files.

## Extending

Add a skill: `plugins/pcb-kit/skills/<name>/SKILL.md` with `name`, `description`, `when_to_use`, under 300 lines, heavy content in `reference/`. Add an agent: `agents/<name>.md`. Keep examples generic; no project or company specifics.
