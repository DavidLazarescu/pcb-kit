# System overview (created with every new schematic, kept up to date)

Every board gets a **high-level overview** that lets an engineer who does not know the project
understand what the board does, in one page.

## Content
- What the board is for (one sentence) and what it connects to: external systems, connectors,
  power sources, control interfaces, mechanical parts that matter (heat sink, enclosure).
- Functional blocks as boxes with the main signal and power flow as arrows, labelled with the key
  numbers (voltages, currents, bus and address, isolation barrier, power dissipation).
- Isolation barriers and ground domains drawn as such.
- Where each block lives in the schematic (sheet name) so the reviewer can jump there.
- Status line: date, schematic revision or commit it matches.

## Form
- Preferred: a vector PDF next to the schematic PDF (`<Board>_overview.pdf`), generated from a
  source file kept in the repo (Graphviz `.dot` or hand-written SVG → `rsvg-convert`), so it can be
  regenerated and diffed. Konnect has no rectangle or image tool, so a drawn block diagram inside
  KiCad is not practical; the root sheet carries a short text overview and a pointer to the PDF.
- If KiCad gains a way to draw it cleanly (hierarchical sheet symbols wired by hierarchical pins),
  the root sheet may become the overview instead.

## Keeping it current
- Update the overview whenever a change alters the structure: a block added or removed, a new
  interface or connector, a changed power or isolation concept, a changed sheet split.
  Value changes and redraws do not need an update.
- The verification phase checks that the overview's status line matches the current schematic.
