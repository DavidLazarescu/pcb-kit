---
name: pcb-verify
description: Independent verification of a KiCad schematic with kicad-cli: netlist export and netcompare against a saved baseline, ERC JSON, BOM field check, critical-pin review, island check, rendered review. ERC 0 does not prove correctness. Use after any schematic build, rework, agent abort or cosmetic change.
when_to_use: A schematic changed, an agent aborted, or the user asks whether the schematic is correct or ready.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/60-verification.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/60-verification.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Verify

Invoke `konnect` and `kicad-review` as needed. Reads use exports (kicad-cli), never file edits.

## Inputs
Root `.kicad_sch`, `SCHEMATIC_SPEC.md`, baseline netlist in `verify/` if one exists.

## Steps
1. Read the rule layers above.
2. Run `${CLAUDE_PLUGIN_ROOT}/tools/verify.sh <root.kicad_sch> [baseline.net]`. It writes the ERC JSON, netlist and BOM into `verify/out/` and prints a summary.
3. With a baseline: `IDENTICAL CONNECTIVITY` is expected after cosmetic work. After intended changes the diff must be exactly the intended nets. Any other diff is an error.
4. ERC: read violation types. Fix dangling wires, duplicate references, unconnected pins; justify the rest.
5. BOM: every part has Manufacturer, MPN, Supplier, Supplier Part, Datasheet. Footprints present.
6. Critical-pin review against the spec: isolation barrier pins, IC supplies, enable/reset/default-state pins, island grounds. See [reference/checklist.md](reference/checklist.md).
7. Island check: no net contains both ground names. Duplicated net names across sheets are intended only for global labels.
8. Render sheets (`kicad-cli sch export pdf`) and look at them.
9. When accepted, save the netlist as `verify/netlist_baseline_<date>.net` and commit.
10. Use `schematic-verifier` for an independent pass; the builder never verifies its own work.
11. Report what was checked and what was not.

## Gate (done when)
- [ ] Netlist matches spec on all critical nets
- [ ] netcompare as expected
- [ ] ERC findings resolved or justified
- [ ] BOM fields complete
- [ ] Baseline saved and committed

## Outputs
`verify/netlist_baseline_*.net`, summary in `DESIGN.md` status.

## Pitfalls
- ERC 0 with a bridged isolation barrier after a half-finished rework.
- Trusting Konnect's own readback instead of an independent kicad-cli export.
- Skipping netcompare because "only cosmetic".

## Also read
- `${CLAUDE_PLUGIN_ROOT}/rules/45-schematic-review-layout.md` (uniform fields, horizontal text, review structure)
- `${CLAUDE_PLUGIN_ROOT}/rules/41-system-overview.md` (overview PDF, update on structural change)
