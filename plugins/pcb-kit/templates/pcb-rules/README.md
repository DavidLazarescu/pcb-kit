# pcb-rules (project overrides)

Each file here overrides or extends the kit rule of the same name (`rules/<phase>.md` in the plugin). Order of precedence: kit `00-house-standards.md`, kit phase file, project `00-house-standards.md`, project phase file. Later wins. A skill states conflicts to the user instead of resolving them silently.

Write only differences and additions. Delete a file's body to fall back to the kit rule.
