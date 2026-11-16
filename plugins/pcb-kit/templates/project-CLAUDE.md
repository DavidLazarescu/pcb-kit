# <project> PCB rules

This project uses the `pcb-kit` plugin (KiCad 10 + Konnect). Start with the `pcb-workflow` skill.

- Konnect only; never text-edit KiCad files. KiCad must not have the file open during agent work.
- Commit before any agent rework of a KiCad project.
- Layers: kit rules, then `pcb-rules/` of this project (later wins).
- Boards: `Boards/<board>/Hardware/`; documents: `docs/<board>/`.
- Reusable parts: `parts-registry.md`.
- Tool friction goes to `~/Work/pcb-feedback/<board>.md` while it happens (kit `rules/05-tool-feedback.md`), never into this repo.
- Language of documents: English.
- Project specifics: <supplier, assembler rules, fab house, library paths>
