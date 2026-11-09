# Changelog

## 0.1.0
- Initial kit distilled from two projects: house standards, nine phase rules, eleven skills, three agents, templates, tools (verify.sh, netcompare.py, thermal.py), KiCad text-edit blocking hook.
- Layout skills (70, 80) are thin; extend after the first layout.
- 2026-11-09: rules 41 (system overview PDF, kept current on structural change) and 45 (uniform field placement, horizontal text, review-ready structure); wired into workflow gates, build and verify skills.
- 2026-11-09: rule 45: symbols clean and simple, stdlib style, render check for custom symbols.
- 2026-11-09: footprint verification: rule 25 (record, fpcheck, second source, 3D model, paper print), `parts/` registry, `fpcheck.py`, `fpdiff.py`, `bom_fpcheck.sh` (PASS/FAIL/NO-RECORD/MISSING-3D), gates in phases 20 and 90.
