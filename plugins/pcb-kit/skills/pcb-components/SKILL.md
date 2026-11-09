---
name: pcb-components
description: Selects and verifies PCB components with DigiKey: exact MPN with packaging suffix, stock, lifecycle, datasheet values, footprint check, default-state traps (DAC reset variants, sensor power-up thresholds, heat-sink Rth), parts reuse, removed-or-kept table. Use when choosing parts, building a BOM or checking stock.
when_to_use: Part selection, BOM building, stock or price checks, footprint checks, or reusing parts from earlier boards.
---

## Rule layering

Before starting, read in this order. Later layers override earlier ones. State conflicts to the user instead of choosing silently.
1. `${CLAUDE_PLUGIN_ROOT}/rules/00-house-standards.md` and `${CLAUDE_PLUGIN_ROOT}/rules/20-components.md`
2. The project's `pcb-rules/00-house-standards.md` and `pcb-rules/20-components.md` if they exist (project root = nearest folder containing `pcb-rules/`, else the git root).

# Components

## Inputs
Requirements, `parts-registry.md`, datasheets in `datasheets/`.

## Steps
1. Read the rule layers above.
2. List functions needed. For each, check `parts-registry.md` first and reuse.
3. Shortlist candidates; choose by function, availability, price, package (0603 where possible).
4. Verify each with the DigiKey method in `rules/20-components.md` (WebFetch, detail page, exact MPN with suffix, stock + date, marketplace flag, lifecycle). Delegate bulk lookups to the `part-researcher` agent (haiku) with a precise brief and a table output.
5. Get datasheets; if the site blocks download, ask the user to place the PDF in `datasheets/`.
6. Go through the trap list in [reference/traps.md](reference/traps.md) for every active part.
7. Check each footprint against the datasheet land pattern; prefer the KiCad stdlib. Note symbol gaps.
8. Fill the BOM in `DESIGN.md` with stock, date, price, status.
9. Write the "removed / kept and why" table. Price and KISS review: strike parts without a requirement behind them.
10. Update `parts-registry.md` with parts that will be reused.

## Gate (done when)
- [ ] Each BOM line: exact MPN incl. suffix, stock + date, datasheet saved
- [ ] Traps checked per active part
- [ ] Footprints checked or flagged
- [ ] Removed/kept table written
- [ ] Not-for-new-designs parts have a fallback

## Outputs
BOM, `datasheets/`, registry update, removed/kept table.

## Agents
`part-researcher`.

## Pitfalls
- Summaries mis-attribute stock to substitutes; trust only the detail page.
- Stock goes stale; re-check on the order day.
- Distributor parametric fields can be wrong (heat-sink Rth).
