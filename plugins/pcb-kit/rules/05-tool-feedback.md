# Tool feedback (all phases)

Record friction with Konnect, KiCad and the kit while it happens, so the tools can be improved later. This is not the design log: decisions stay in DESIGN.md.

## Where
- `~/Work/pcb-feedback/<board>.md` (or `$PCB_FEEDBACK_DIR/<board>.md`), one file per board, kept across sessions. Create it from `${CLAUDE_PLUGIN_ROOT}/templates/TOOL_FEEDBACK.md` when it is missing.
- Outside every project repo. Never commit it and never copy it into a repo, an issue or a pull request.
- The kit's hook writes `auto/<date>_<session>.jsonl` there by itself: Konnect tool errors, Konnect responses over 10 kB, and Bash calls that run pcbnew or kipy Python. Do not copy those into the board file. Add an entry only when you know something the hook cannot see (why it happened, what it cost, what tool would have helped).

## When to write an entry
Write it at once, not at the end of the session. Context gets compacted and sessions get cut off.
- A tool is missing, so a script, the GUI or the user had to do it.
- A tool failed, refused unexpectedly, or did something other than its description says.
- A workaround was used: a pcbnew or kipy script, a closed-file edit, an extra export to see something.
- The user had to do something by hand (GUI step, download, setting, check in the 3D viewer).
- A result turned out wrong later (found by verify, a render, netcompare, DRC or a review) after it was reported as done.
- A review correction that a deterministic check could have found.
- A response was far larger than needed, or a simple task took many calls.
- A tool description or skill misled you.

## Entry format
```
## <YYYY-MM-DD HH:MM> · <phase> · <missing | failed | workaround | manual | wrong-later | review | cost | docs>
Wanted:     what you were trying to do
Happened:   what the tool did, with tool name and error kind or message
Workaround: what you did instead (or "none")
Cost:       minutes, and "human needed" if the user had to act
Suggestion: the tool or change that would have avoided it
```
Facts, not blame. Name the tool, the error kind and the object. One entry per problem; when the same problem comes back, add a line `Again: <date>, <where>` to the first entry instead of a new one.

## Phase retrospective at every gate
Before passing a gate in `pcb-workflow`, append:
```
## <YYYY-MM-DD> · retrospective · phase <NN>
Time sinks:     the three biggest, with rough hours
User steps:     how many times the user had to act, and for what
Would have helped: tools or checks, most valuable first
```
