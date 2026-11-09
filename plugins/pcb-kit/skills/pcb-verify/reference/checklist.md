# Verification checklist

- [ ] kicad-cli netlist exported fresh from the current files
- [ ] netcompare against baseline run; differences explained
- [ ] ERC JSON reviewed by type
- [ ] BOM exported; all five fields set on every part
- [ ] Isolation barrier: each pin of the isolator and isolated converter on the right side
- [ ] Every IC supply pin on the intended rail (isolated versus port side)
- [ ] Decoupling capacitors on the correct rail pair
- [ ] Enable, reset, address and default-state pins match the design
- [ ] Bus lines have pull-ups on the correct rail; address collisions checked
- [ ] Island grounds distinct; no net with both
- [ ] Unused pins: explicit no-connect or tie per datasheet
- [ ] Sheet PDFs rendered and read: overlaps, dangling wires, unreadable notes
- [ ] Reference designators unique; `#PWR` unique
