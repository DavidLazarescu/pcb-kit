# PCB layout digest for a KiCad/AI-agent layout process
Read/compiled 2026-11-11. Boards: small mixed-signal, 2 layers, JLCPCB.
Tags: [P] primary source read this session; [S] only search-result snippet (not read in full); [V] vendor blog/forum (supporting only);
[G] general engineering knowledge, no source retrieved (flagged, verify); [C] computed here from a stated formula.
Several primary sources (ADI MT-031/MT-101, Hartley IPC deck, TI SLYT499/512, TI SLLA284 sect. 4, ROHM AN PDF) could not be read
(timeouts / compressed PDF); where only the title/snippet was seen it is marked [S].

## 1. Process order and AI/script-driven layout

### 1.1 Order of work (consensus of vendor/tutorial sources; no standard prescribes it)
1. Board setup first: design rules, net classes, stackup, layer roles before any placement. KiCad docs: "establish all known design rules at the
   beginning of the board design process"; Board Setup constraints are absolute minimums that net-class rules cannot go below. [P] https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html
2. Outline, mounting holes, connectors and mechanically fixed parts first, aligned to cutouts/mating positions, then LOCK them. [S] https://www.protoexpress.com/kb/pcb-component-placement-rules/
3. Protection (ESD/TVS/fuse) directly behind the connector it protects. [S] same Proto Express source.
4. Power conditioning, then critical ICs (precision analog, isolators, MCU), then the passives. Ordering "mechanical/connectors locked -> power -> critical -> passives" [S] https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/
5. Decoupling caps are placed with their host IC (at the pin), not as generic passives. [S] same. A cap 10 mm from the pin gives almost no benefit above 100 MHz [S] (same source set).
6. Only after fixed + critical parts are placed and locked: support parts, then routing. [S] Proto Express.
7. Route order (from the Microchip 2-layer guidance and the sense/power sources below): ground concept (pour or grid) decided/placed FIRST, then
   critical nets (sense lines, precision analog inputs, high-current paths), then power, then bus/digital, then the rest. Microchip: "It is very
   important to first put the ground grid in place"; every board area should have ground coverage on at least one layer. [P] https://onlinedocs.microchip.com/oxy/GUID-52972CAB-8C1D-44E1-99A1-4899C2769960-en-US-2/GUID-FCA6F4C8-473A-497F-A0AE-42F4DEE9B54F.html
8. Anecdote only: "60 % placement / 40 % routing" effort split. [V] pcbsync.com/pcb-component-placement/ (single blog; do not cite as a rule).
9. Placement and routing are coupled: placing everything first then routing (autorouter habit) fails when one region is congested; the useful AI
   contribution in one report was spotting that all unrouted nets ended in one region and suggesting a re-stagger of parts. [V] https://www.quilter.ai/blog/llm-pcb-layout-gpt-6-astra ; [P] https://tinycomputers.io/posts/what-routing-314-nets-taught-me-about-ai-assisted-pcb-design.md
   => Process rule: allow a "placement revisit" gate when routing leaves >N unrouted nets in one region, instead of forcing routes.
10. Review checkpoints (synthesis): (a) after placement, before any trace; (b) after critical nets; (c) after full route + pour; (d) before fab
    outputs. Each checkpoint = DRC via kicad-cli + rendered view + human look (see sect. 8).

### 1.2 Published experience with AI / script-driven KiCad layout
- Self-reports are unreliable: all 27 agent sessions reported a complete job; the independent checker found only 1-8 nets actually routed. Judge
  with deterministic code / `kicad-cli` DRC, not with the model; pin the exact DRC invocation because repeated runs on identical files gave slightly
  different totals on some boards. [P] https://forum.kicad.info/t/two-months-of-testing-llms-on-pcb-autorouting-what-worked-what-didnt-and-whats-left-to-try-open-archive/72250
- Same study: model as evaluator + deterministic engine as router worked ("the model evaluates, deterministic engine routes"). Model-chosen net order
  gave -2.75 % to 0 % gain; models drawing copper directly fully connected 0 of 3 boards; structured text (layer occupancy, netlist adjacency) gave
  0.82 recall vs 0.03 for an SVG image of the same board => feed the agent coordinates/tables, not screenshots, for analysis. [P] same.
- Multi-round probe-style guidance reached optimum in 4/5 small scenarios; one-shot blind proposals 0/5. [P] same => iterate with DRC feedback in small steps.
- Script-generated board + AI audit vs datasheet + Freerouting + multi-tool DRC + fab DFM check worked for a 314-net digital board; AI audit caught a real
  bug that the AI itself had introduced; mostly cosmetic otherwise; AI "biased toward continuing the task" (no sense of when to abandon an approach);
  a tool's save routine silently altered the layer-stack (5 instead of 4 copper layers). Treat the fab's DFM as authoritative; validate the
  pipeline on a toy board first. [P] https://tinycomputers.io/posts/what-routing-314-nets-taught-me-about-ai-assisted-pcb-design.md
- Freerouting beat the author's LLM-built router: 8-12 % shorter tracks, 70-97 % fewer vias, ~12 s vs hours (same KiCad-forum study). [P]
- Practitioners (EEVblog): LLM has no real visual layout sense; design intent (diff pairs, noise, current paths, orientation) is not in the netlist;
  work with small verifiable tasks, write constraints + datasheet excerpts into a markdown file, keep files in git, positive phrasing; LLM useful for
  review/BOM/footprints/calculations, not core layout decisions. [P] https://www.eevblog.com/forum/eda/claude-code-for-pcb-design/
- Open: no MCP-specific failure-mode reports found.
- Implications for the toolkit (synthesis): lock fixed parts; every agent step ends with an automated check (DRC, unconnected count, clearance report)
  whose output, not the agent's claim, gates progress; give the agent explicit written net rules (width, clearance, class) rather than intent prose;
  re-read board state from file after each batch; keep human review at checkpoints 1.1(a)-(d).

## 2. Grounding and return currents on 2-layer boards
- Return current follows the least-inductance path, at HF directly under the signal trace; loop area sets inductance/radiation; a cut/slot in the
  return path forces the current around it and enlarges the loop. [S] https://incompliancemag.com/alternative-paths-of-the-return-current/ ; https://digital.incompliancemag.com/issue/november-2020/pcb-return-current-distribution-in-a-microstrip-line/
- Rule: dedicate one layer (bottom) to ground; route signals on top only. Every signal trace should have ground copper beneath it; routing signals
  in the ground layer disrupts return paths and each such crossing has to be analysed. [P] Microchip two-layer page (URL in 1.1).
- If bottom cannot be a full plane: ground grid, placed first, cells smaller / tracks wider for higher current/frequency; weaker than a plane but
  better than routing GND like a signal. Fill unused area on both sides and stitch with vias; no area without ground coverage on at least one layer. [P] Microchip.
- Ott (Electromagnetic Compatibility Engineering, sect. 10.5.3): two-layer gridded ground vs single-point ground ~7 dB lower radiation (as reported
  secondhand; not checked against Ott's text). [S] https://www.allaboutcircuits.com/technical-articles/multipoint-grounding-gridded-ground-for-double-sided-pcbs/
- Caveat: grids/fill can form conductive loops around components; "power finger" two-layer layouts give large return loops - avoid. [S] same AAC/Ott snippets.
- Slots: do not run signal traces over gaps in the ground pour; avoid thin necks/islands (acid traps and return detours). Keep any slot for isolation
  clear of signals except those that must cross (and then isolated ones cross only through the isolator). [S] pcbsync.com/i2c-bus-pcb-layout (I2C text: "do not let either trace cross a plane split").
- Mixed-signal single plane: TI Grounding in Mixed-Signal Systems Demystified (Part 2, 2Q 2013): "always preferable to use only one ground plane,
  partitioning the PCB" into analog and digital areas rather than separate planes; ground connected at a single star point generally at the supply
  / under the converter; with several converters, multiple star points create loops. [S] https://ti.com/lit/slyt499 and https://ti.com/lit/pdf/SLYT512 ; summary via https://www.arrow.com/en/research-and-events/articles/principles-of-grounding-for-mixed-signal-designs
  Note: Arrow page could not be opened (timeout), snippet only.
- Digital return currents flowing through the analog area degrade high-resolution converters (TI Part 1). [S] same.
- Efforts to reconnect separated ground shapes are "often not as effective as making the original solid connections". [S] https://incompliancemag.com/?p=35808
- Altium note: star ground is sound in theory, hard to realize in hardware. [S] https://resources.altium.com:443/sites/default/files/uberflip_docs/file_1214.pdf
- Separating a high-current return from precision analog ground (synthesis, [G] + sense sources below): partition by placement, not by cut. Put the
  power stage and its return loop in one region (e.g. one end of the board), precision analog on the other; let the high current return flow in its
  own copper path (wide pour) straight from load/connector back to the supply, never through the analog area; join the regions at ONE neck/star
  point (near the supply entry or under the ADC / reference), and bring the sense resistor's Kelvin sense lines to the amplifier's ground there.
  The current-sense resistor itself belongs on the high-current return path; its sense leads are the only "analog" connection to it.
- ADI "Reducing ground bounce in DC-DC converters": on 2-layer, build the input cap + switches over a ground island; keep high di/dt loop tiny. [S] https://www.analog.com/en/resources/analog-dialogue/articles/reducing-ground-bounce-in-dc-to-dc-converters.html
- Stitching vias [G, no primary retrieved]: tie top and bottom ground pours with vias every ~5-10 mm and along edges, plus 1-2 vias next to every
  ground pin/cap; at isolation barriers do NOT stitch across the barrier. Verify numbers against a retrieved source before encoding as hard rules.
- KiCad: after any change, refill all zones (B key / `kicad-cli pcb drc` fills? check -- DRC against stale fills gives false results) [G].
- Where to join grounds: one place, close to where the power enters / the ADC sits; AGND/DGND bridge ("bridge, sometimes called star ground") [S] Arrow/TI above.

## 3. Decoupling, I2C, LED/test points
### Decoupling
- Cap at the IC power pin; route IC pin -> cap pad -> via to plane. Do NOT put the via between IC and cap (puts via inductance in the HF loop).
  [S] https://jlcpcb.com/blog/the-definitive-guide-to-bypass-capacitor-in-pcb-layout
- Keep each cap's power and ground vias as close as possible to their pads; both vias on the same side of the cap shrinks loop area; short wide
  connections, no long traces on the cap. [S] https://www.intel.com/content/www/us/en/docs/programmable/683073/current/mounting-inductance.html ; https://learnemc.com/decoupling-for-boards-with-widely-spaced-planes
- Minimise loop area; limit pad sizes so vias can move closer. [S] https://johansondielectrics.com/x2y-power-bypass-pcb-mounting
- Cap far from pin (10 mm) gives negligible HF benefit. [S] Proto Express set (see 1.1).
- 2-layer specific [G]: where no plane is under the cap, use a short direct ground trace/pour connection on the same layer; the smallest loop is IC
  VDD pin -> cap -> IC GND pin; the bulk cap sits at the supply entry of each block, small (100 nF) caps at each IC. Datasheet layout guidelines of the specific IC override these.
- Thermal relief on cap ground pads is acceptable; the loop matters more than the relief spokes [G].
### I2C
- SCL/SDA as short as possible and narrow (e.g. 5-10 mil) to limit capacitance; keep both lines' lengths close. [S] https://www.ti.com/document-viewer/TPL0401B-10/datasheet/layout ; https://www.ti.com/document-viewer/lit/html/SCPS238A/GUID-88D0FF57-6BCA-4CCE-85BA-45B8BFDED3B7
- No impedance matching / diff-pair rules needed at I2C speeds (TI TCA9846). [S] https://www.ti.com/document-viewer/lit/html/SLVSLJ5A/GUID-45BA336F-63C4-4DD0-94FB-E2F99ABE9AF5
- Route next to unbroken ground, close together, never across a ground split. [V] https://pcbsync.com/i2c-bus-pcb-layout/
- Bus capacitance limit 400 pF (Std/Fast), 550 pF (FM+); ~1-2 pF/cm trace over ground (rough figure). [V] same.
- Exactly one set of pull-ups per bus (duplicate pull-ups from each module is a common mistake). [V] same. Pull-up location: AMD puts them at the far end, vendor-specific; no general rule. [S] https://docs.amd.com/r/en-US/ug863-versal-pcb-design/I2C
- Isolated I2C (e.g. ISO1640): see TI SLLU322A layout. [S] https://ti.com/document-viewer/lit/html/SLLU322A/GUID-98286EA0-FAE6-4B84-AFBB-7530ED0571E5 (not read).
### LEDs and test points
- No retrieved primary source. [G] LED + series resistor near the signal source, reference designator and function label ("PWR", "FAULT") on silk; test
  points on top, 1.5-2 mm apart or at least a probe-clip pitch, on the nets named in the bring-up plan (rails, GND near each analog block, I2C lines,
  sense nodes), never on the Kelvin sense lines in a way that adds stubs (tap via a series resistor / short stub), a GND test point beside each
  rail test point. Mark as UNVERIFIED until a source is added.

## 4. High-current DC
### Trace width (1 oz = 35 um external)
- IPC-2152 is the current standard, but the data are nomographs in a paid document, not a formula; free web calculators mix 2221 and 2152 and disagree.
  pcbsync: "IPC-2152 ... No longer maintained [orig. 8/09]"; plane proximity, dielectric and adjacent heating affect results; data for 10-100 C rise, most
  designs use 10-20 C. [P] https://pcbsync.com/ipc-2152/
- Altium table labelled IPC-2152, 1 oz, 10 C rise, FR4: 3 A -> 50 mil (1.27 mm); 5 A -> 110 mil (2.79 mm). [P] https://resources.altium.com/pcb-design-blog/pcb-trace-width-vs-current-table-for-high-voltage-design
  (note the 2152 nomograph itself covers internal traces; the values match IPC-2221 external almost exactly, i.e. probably 2221 labelled 2152. [P], inference mine.)
- IPC-2221 external formula (k=0.048, dT^0.44, A^0.725), 1 oz, computed by NextPCB: [C/P] https://www.nextpcb.com/blog/pcb-trace-width-calculation-high-current-design-and-thermal-analysis
  | Current | dT 10 C | dT 20 C |
  | 3 A | 54 mil = 1.36 mm | 35 mil = 0.90 mm |
  | 5 A | 109 mil = 2.77 mm | 71 mil = 1.81 mm |
- Other sources contradict (AtlasPCB, 20 C, "IPC-2152"-style: 3 A 0.64 mm, 5 A 1.14 mm; PCBSync 20 C: 3 A 50 mil, 5 A 100 mil) [V] https://atlaspcb.com/blog/pcb-trace-width-current-capacity .
  => NO verified IPC-2152 number for 20 C. Recommended process default: design to the 10 C column (3 A >= 1.4 mm, 5 A >= 2.8 mm), use a pour
  or 2 oz where space allows, verify the real temperature rise on the first board.
- Pours instead of traces: a pour/pad with two layers in parallel (top + bottom via-stitched) halves resistance; above 5 A use multiple layers in
  parallel or 2 oz copper. [P] https://stackpole-europe-website.pages.dev/article-kelvin-layout (statement made in the sense-resistor context). Narrow necks in a pour set the limit: check every neck width, not average width. [G]
- Keep high-current traces short; resistance of 1 mm x 10 mm in 1 oz ~ 5 mOhm (Stackpole [P]); 1 oz copper ~ 0.5 mOhm per square [G] (rho 1.7e-8, 35 um).
### Vias
- Barrel area ~ pi x D x t; 0.3 mm drill x 25 um plating = 0.024 mm2 (0.035 mm gives 0.033 mm2). [S, formula] https://forum.kicad.info/uploads/short-url/sYJ0yupiFe5zKhudZZTRkGaemRc.pdf (via current discussion).
- Reported ratings: ~1.9 A per 0.3 mm via at 10 C rise (Flux calc, 25 um plating); ~1.5 A (AllPCB). [V/S] https://www.allpcb.com/allelectrohub/via-in-pad-current-carrying-capacity-a-detailed-guide . "A drilled diameter alone does not establish a safe current rating"; parallel vias do not always share equally [P] pcbsync IPC-2152 page.
- Planning rule (mine, conservative): 1 A per 0.3 mm via; 5 A = >= 6 vias, spread, with at least one via per ~1 A and placed at the pad edge, not stacked on one side.
- JLCPCB plating: not retrieved this session [unknown]; use ~20-25 um.
### Thermal relief vs solid
- Reliefs help hand soldering but limit current; sources recommend solid connection for high-current power pads (one puts the threshold >3 A continuous),
  fix soldering by preheat; a relief adding 3 mOhm dissipates noticeably at 10 A. Spoke starting range 0.2-0.5 mm for standard boards; total spoke width should
  match the required trace width. Set per pad function: signal/ground relieved, power pads solid. [V] https://jlcpcb.com/blog/thermal-relief-pad-design ; https://www.aivon.com/blog/pcb-design/high-current-pcb-design-how-thermal-relief-impacts-power-delivery
- KiCad: DRC flags a pad whose thermal relief has fewer spokes than the minimum set in Constraints (zone connection per pad/zone). [P] https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html (other KiCad zone details not verified).

## 5. Kelvin routing of a 2-terminal sense resistor (2512)
- Kelvin matters when R is below the resistance of ~10 mm of trace at your width; below ~10-20 mOhm it matters; 1 mm x 10 mm 1 oz trace ~ 5 mOhm. [S/P] Stackpole https://stackpole-europe-website.pages.dev/guide-shunt-layout and https://stackpole-europe-website.pages.dev/article-kelvin-layout
- Sense tap originates at the pad edge nearest the resistor body (inside edge), never partway along the force trace; sense pad about 0.5-0.8 mm wide, 0.15 mm
  gap to the force pad; separate mask openings; no paste on the sense pad; force and sense never share a via. [P] Stackpole Kelvin article.
- Alternative: TI SBOA197: if the resistor value is specified at the inside of the pads, inside-pad connection gives the best match; BQ27545 datasheet:
  connect differential traces at the inside of the sense resistor pads. Check the resistor datasheet for where its value is measured. [S] https://www.ti.com/lit/pdf/sboa197 (PDF unreadable; snippet via search) ; https://www.ti.com.cn/document-viewer/cn/BQ27545-G1/datasheet/180-ZHCSAB6E
- ADI: standard 2-terminal footprint must be divided so system current and sense current have separate paths; compares outer vs inner pad-edge sense points. [P/S] https://www.analog.com/en/resources/analog-dialogue/articles/optimize-high-current-sensing-accuracy.html (fetch timed out; snippet only)
- TI LMP8640: 4-wire connection at a point not within the direct high-current path; give the resistor lots of copper for heat (value drifts with temperature). [S] https://ti.com/document-viewer/LMP8640-Q1/datasheet/layout
- Routing: thin matched pair (~0.1-0.15 mm), side by side (differential routing), >= 0.5 mm from any conductor carrying > 1 A, length mismatch ~1 mm ok, > 5 mm risk of noise
  pickup; keep clear of switching nodes; amplifier within ~10-15 mm of the resistor. [P] Stackpole.
- Filter: matched series pair 10-22 Ohm plus ~100 pF C0G across the amplifier inputs, placed AT the amplifier, with the matched resistors identical on both legs. [P] Stackpole. (Series R adds offset with bias current: keep small. [G])
- Force pads of a 2512 at 5 A: >= 2 mm wide connection; high-current copper wide + short; keep sense traces off the force pour (no ground pour merging with the sense pad). [P] Stackpole.
- Preferred if allowed: true 4-terminal sense resistor (Bourns). [S] https://www.mouser.lt/pdfdocs/bourns_n1702_current_sense_accurate_measurement.pdf
- ROHM PCB layout guide for shunt resistors exists [S] https://fscdn.rohm.com/en/products/databook/applinote/common/pcb_layout_guide_for_sensing_circuits_using_shunt_resistors_an-e.pdf (unreadable here).

## 6. JLCPCB 2-layer capabilities (read 2026-11-11)
Source pages: https://jlcpcb.com/capabilities/Capabilities and https://jlcpcb.com/capabilities/pcb-capabilities (footer "(c) 2026 JLCPCB", no "last updated" date). [P]
| Item | Value |
|---|---|
| Board thickness options | 0.4/0.6/0.8/1.0/1.2/1.6/2.0 mm in table (page also lists 0.4-4.5; FAQ says 0.4-3.2: page is inconsistent). No default stated on page; 1.6 mm is the usual order default [G] |
| Thickness tolerance | +-10 % (>=1.0 mm); +-0.1 mm (<1.0 mm) |
| Outer copper, 2-layer | 1 / 2 / 2.5 / 3.5 / 4.5 oz (multilayer 1/2). Inner default 0.5 oz. Outer default not stated; 1 oz is the standard order [G] |
| Min track/space, 1 oz | 0.10 / 0.10 mm (4/4 mil); 2 oz: 0.16 / 0.16 mm; width tol. +-20 % |
| Via (2-layer) | min hole/diameter 0.15 / 0.25 mm standard; preferred min hole 0.2 mm; via dia 0.1 mm larger than hole (0.15 preferred). 0.1 mm drill: "more costly". 0.2/0.25 hole with via dia < 0.45 mm costs more; 0.1/0.2 vias only <= 1 mm board with ENIG/OSP |
| Annular ring PTH 2-layer 1 oz | recommended >= 0.25 mm, absolute min 0.18 mm (general PTH >= 0.20 mm; multilayer 0.20/0.15); 2 oz: 0.254 mm. NPTH pad >= 0.45 mm |
| Min SMD pad | 0.25 x 0.25 mm |
| Hole-to-hole | via 0.2 mm; pad 0.45 mm |
| Copper to routed board edge | >= 0.2 mm; V-cut >= 0.4 mm; mouse-bite >= 0.2 mm; castellated holes >= 1 mm from edge |
| Silkscreen | line width >= 0.15 mm; text height >= 1.0 mm (40 mil); width:height 1:6; pad-to-silk 0.15 mm |
| Solder-mask bridge | 0.10 mm (1 oz, green/red/yellow/blue/purple), 0.13 mm (black/white), 0.20 mm (2 oz); mask opening to neighbouring trace >= 0.09 mm; expansion 1:1 |
| Slots | plated >= 0.5 mm (2-layer), non-plated >= 1.0 mm; NPTH hole >= 0.5 mm |
| Er | "FR-4 dielectric constants 4.5 (2-Layer PCB)"; prepreg 7628 4.4, 3313 4.1, 2116 4.16 (impedance page lists core 4.6, 1080 3.91, mask 3.8). https://jlcpcb.com/impedance has NO 2-layer stackup (only 4/6 layer) |
| Stackup 2-layer 1.6 mm | no official layer thicknesses published; unofficial (JLC3DP support, not JLCPCB): ~1.5 mm core + 35 um Cu each side. https://jlc3dp.com/help/answers/detail/15-various-stackups |
| Surface finish | HASL (leaded/lead-free), ENIG, OSP (OSP not for single-sided) |
Standard vs extra cost as stated: 0.1 mm drill and small via-diameter combos above cost extra; 2 oz and up, ENIG, non-green masks may cost extra (not stated on page; check order form). Via-in-pad = filled/capped vias (default 6-layer+). Min board 3x3 mm.
Design defaults for the toolkit (synthesis, with margin): track >= 0.2 mm (0.127 min only where needed), clearance >= 0.2 mm, via 0.3 drill / 0.6 pad (ring 0.15; JLC min 0.18-0.25 for 2-layer 1 oz so use >= 0.7 mm pad if ring 0.2 desired), copper-to-edge >= 0.3 mm, silk 0.15 mm line / 1.0 mm text min (use 0.8 mm stroke? no: width 0.15, height >= 1.0, 1.0 mm recommended minimum 1.2 for readability [G]).

## 7. Silkscreen and documentation
- Reference designators outside the component courtyard/body, close to their part; text under a part is lost after assembly. [V] https://www.flux.ai/p/blog/pcb-silkscreen-design ; https://resources.altium.com/p/your-guide-pcb-silkscreen
- Pin 1 marked with dot/triangle/notch, not hidden under the IC body; connectors: label pin 1 and function of each pin; diodes, electrolytic caps, LEDs: polarity (K/A, +). [V] same.
- Board name, revision and date code on silk so nobody tests old hardware. [V] same. IPC: manufacturer mark/lot number [V, not verified]. 
- High-voltage areas: lightning-bolt warning near hazardous voltage; no regulatory specifics found. [V] Flux/Altium. Isolation barrier marking: none found in sources;
  [G] mark the barrier with a silk line along the gap and label each side ("ISOLATED / FIELD SIDE" vs "LOGIC SIDE") and name the nets' grounds (GND vs GND_ISO). Mark UNVERIFIED.
- Silkscreen must not overlap pads/vias/mask openings (JLC pad-to-silk 0.15 mm), use >= JLC min line/text (sect. 6); no silkscreen on test points. [P] JLC page.
- Keep silk >= 0.5 mm from sensitive RF/high-speed traces (rule of thumb only). [V] Zbotic/Flux.
- JLC part marking on the board (e.g. order number) can be removed by paying extra [G, not verified in this session].
- Isolation barrier spacing is governed by the equipment standard (working voltage, pollution degree, material group), not by the isolator datasheet; the isolator pad layout must not reduce package creepage/clearance; grooves/slots under the chip can add creepage; the PCB material
  grade is usually lower than the package's. [S] https://e2e.ti.com/support/isolation/digital_isolators/f/1013/t/625892 ; TI SLLA284 sect. 4.3 (creepage) not read: https://ti.com/lit/pdf/SLLA284
  Practical: no copper (including pours, silk-less traces, stitching vias, test points) in the barrier gap; keep the gap uniform across the full isolator width; shape pours to the required creepage; no components bridging the barrier except
  rated ones (isolator, Y-cap, transformer). [G] verify the voltage-based number from the applicable standard (e.g. IEC 60664-1 / IEC 62368-1 / IPC-2221 spacing table) once the working voltage is known.

## 8. Layout review checklist (synthesis; source section in brackets)
1. DRC clean via kicad-cli after zone refill; unconnected = 0; the report is shown, not summarised by the agent. [1.2]
2. Design rules in KiCad match JLC capabilities (sect. 6) with margin; no rule below the JLC minimum. [6]
3. Fixed items (connectors, holes, outline) were placed first and are locked; mating positions and cutouts checked. [1.1]
4. Protection parts sit directly behind the connector they protect. [1.1]
5. Placement groups are physically separated: power stage / precision analog / digital / isolation barrier. [2]
6. Each IC has its decoupling cap at the pin, via next to the cap pad, not between IC and cap, power+ground vias close together. [3]
7. Bottom layer is a continuous ground pour; no signal traces in it except where unavoidable and analysed. [2]
8. No signal trace crosses a gap/slot in the ground pour; no thin pour necks or isolated copper islands. [2]
9. High-current return path is separate from precision analog ground and joined at one point (named). [2]
10. Top/bottom ground stitching vias exist, none across the isolation barrier. [2]
11. Every high-current net: width >= required (3 A: >= 1.4 mm, 5 A: >= 2.8 mm for 10 C rise; or pour); necks measured. [4]
12. High-current layer transitions use enough vias (>= 1 per ampere at 0.3 mm), power pads solid (no relief) or wide spokes. [4]
13. Sense resistor: tap at the inner pad edge (or per resistor datasheet), separate sense pads, no shared via with force. [5]
14. Sense pair: matched, ~0.1-0.15 mm, side by side, >= 0.5 mm from >1 A copper, no switching node nearby, filter at the amplifier. [5]
15. I2C: short, narrow, equal length, over solid ground, one set of pull-ups only, bus capacitance estimated. [3]
16. Isolation barrier: creepage/clearance for the stated working voltage met everywhere, no copper/test point/via in the gap, uniform across isolator width, documented on the silk. [7]
17. Test points on every rail and key analog node, ground test point beside each, reachable with a probe, not creating stubs on sense lines. [3]
18. Silkscreen: refdes outside courtyards and legible (>= JLC min height/width), no silk on pads, polarity/pin 1/connector pins labelled. [7]
19. Board name, revision, date on silk; barrier marked; HV warning where applicable. [7]
20. Copper to board edge >= JLC min (0.2 mm, use 0.3); mounting holes keep-out as intended. [6]
21. Mask: bridges >= 0.10 mm; sense pads with separate openings. [6]
22. Vias: drill >= 0.3, ring >= JLC minimum; hole-to-hole >= 0.2 (vias)/0.45 (pads). [6]
23. 3D / courtyard check: no part overlaps, connector keepout from enclosure/mating part. [1.1]
24. Placement revisit gate was used if routing congested one region; no forced routes with acute angles or needless narrowing. [1.1, 1.2]
25. Every footprint matches its datasheet land pattern (re-check polarised and non-standard parts). [G]
26. Netlist/ratsnest cross-checked against the schematic after the last change (kicad-cli netlist compare). [1.2]
27. Independent human review of rendered top and bottom views plus 3D at checkpoint (c). [1.1, 1.2]
28. Fab check: JLC DFM/online preview before ordering; fab DFM is the authority. [1.2]
29. First-board bring-up: measure real temperature rise at max current and the actual sense-resistor error. [4,5]
30. Everything in sect. 2-3-7 tagged [G]/UNVERIFIED is confirmed against a retrieved source or by the first board before it becomes a hard rule. 
