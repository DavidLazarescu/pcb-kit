#!/usr/bin/env bash
# PreToolUse hook: block text edits of KiCad source files. Edit/Write/NotebookEdit are checked by
# file path; Bash is checked best effort (sed -i, perl -i, tee, redirection, cp/mv/rm onto those files).
# Limits: shell indirection (variables, scripts, python writing the file) is not detected.
# Exit 2 blocks the call and shows the message to Claude.
input=$(cat)
exts='kicad_sch|kicad_pcb|kicad_pro|kicad_sym|kicad_mod'
msg="Blocked: KiCad source files must not be text-edited. Use the Konnect MCP tools (invoke the konnect skill). KiCad must not have the file open."

read -r tool path cmd < <(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("? - -"); sys.exit()
ti = d.get("tool_input", {}) or {}
p = ti.get("file_path") or ti.get("notebook_path") or "-"
c = (ti.get("command") or "-").replace("\n", " ")
print(d.get("tool_name", "?"), p.replace(" ", "%20"), c)
' 2>/dev/null)

case "$tool" in
  Edit|Write|NotebookEdit)
    if printf '%s' "$path" | grep -Eq "\.(${exts})$|(^|/)(fp-lib-table|sym-lib-table)$"; then
      echo "$msg" >&2; exit 2
    fi ;;
  Bash)
    # Best effort: a write-capable command that mentions a protected file.
    if printf '%s' "$cmd" | grep -Eq "\.(${exts})\b" &&
       printf '%s' "$cmd" | grep -Eq "(sed[^|;&]* -i|perl[^|;&]* -[a-z]*i|tee |>>? *[^ ]*\.(${exts})|\b(cp|mv|rm|truncate|dd|install) )"; then
      # Allow read-only kicad-cli exports that write elsewhere.
      if printf '%s' "$cmd" | grep -Eq "^kicad-cli "; then exit 0; fi
      echo "$msg" >&2; exit 2
    fi ;;
esac
exit 0
