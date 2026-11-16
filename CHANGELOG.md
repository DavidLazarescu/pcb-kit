# Changelog

## 0.1.0
- Initial kit distilled from two projects: house standards, nine phase rules, eleven skills, three agents, templates, tools (verify.sh, netcompare.py, thermal.py), KiCad text-edit blocking hook.
- Layout skills (70, 80) are thin; extend after the first layout.
- 2026-11-09: rules 41 (system overview PDF, kept current on structural change) and 45 (uniform field placement, horizontal text, review-ready structure); wired into workflow gates, build and verify skills.
- 2026-11-09: rule 45: symbols clean and simple, stdlib style, render check for custom symbols.
- 2026-11-09: footprint verification: rule 25 (record, fpcheck, second source, 3D model, paper print), `parts/` registry, `fpcheck.py`, `fpdiff.py`, `bom_fpcheck.sh` (PASS/FAIL/NO-RECORD/MISSING-3D), gates in phases 20 and 90.
- 2026-11-09: fpcheck: unnamed symbol pins (~ / empty) compare equal; records ISO1644/OPA187/74LVC1G04 accept stdlib pin naming. Negative tests (wrong pin count, SC-70 vs SOT-23, TSSOP vs SOIC, narrow vs wide SOIC, SOT-223 tab pin 4, TO-220 vs TO-247) all FAIL as expected.
- 2026-11-09: rule 25: blind-test results and self-built footprint checklist.
- 2026-11-09: footprint intake with the user (rule 25, workflow gate 65), tools/fp_requests.py builds the download list.
- 2026-11-09: rule 25 lessons from the first intake (download pad numbering, STEP length check and scaling, ask for datasheets together with CAD).
- 2026-11-09: rule 70: JLCPCB default stackup, deviations discussed with the user, impedance and current sizing with that stackup.
- 2026-11-09: 25 part records from the cell-voltage emulator board (TI ICs, CPC1017N, MCP1792 5 V, passives with stdlib land noted, MountingHole).
- 2026-11-09: rule 45: tile-level render review (12 tiles at 4200 px) with a defect list, defect criteria, review by someone other than the builder; overview-zoom checks let overlaps and a broken custom op-amp symbol through.
- 2026-11-11: rule 45: split sheets along the signal chain; measurement next to what it measures (EE review).
- 2026-11-11: rule 45: note texts short and explanatory, math only for non-trivial results.
- 2026-11-16: tool feedback log: rule 05 (entries while friction happens, retrospective at every gate), `templates/TOOL_FEEDBACK.md`, hook `log-tool-friction.py` (PostToolUse and PostToolUseFailure: Konnect errors, responses over 10 kB, pcbnew/kipy Bash scripts) writing to `~/Work/pcb-feedback/auto/`.
