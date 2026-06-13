# Quality Report — Classical-Lattice Critical-Temperature Workflow Benchmark

Built 2026-06-13 with the `workflow-benchmark-forge` methodology from the
workflow-family atlas cluster **#10555** "Monte Carlo finite-size scaling for
critical temperature" (128-paper pool; 93 the knowledge-graph service graphs recoverable; 35
unfetched). Second benchmark built with the methodology after the Floquet
suite — this one exercises the **categorical_exact** verifier (new) and has
much higher paper-reported gold density.

## Inventory: 51 records / 3 tracks

| Track | facet | answer type | verifier | train | val |
|---|---|---|---|---|---|
| C1 critical-point ★ | full MC+FSS loop → T_c / K_c | numeric scalar | scalar_tolerance | 14 | 11 |
| C2 critical-exponents | FSS collapse → ν, γ/ν, β/ν, η, z | numeric scalar | scalar_tolerance | 5 | 4 |
| C3 transition-character | order (1st/continuous/BKT) + universality class | categorical | categorical_exact | 9 | 8 |

C1 is the flagship (the full 6-step workflow incl. the finite-size
extrapolation outer loop). C2 (9 records) is slightly under the ≥10 floor →
marked **preliminary**. Splits stratified by model_family.

## Cohort scan (93 papers classified by main output)
critical_temperature 47 (45 numeric) · transition_character 20 (16) ·
critical_exponent 11 (11) · analytic_reference 1 · other 14.
**Paper-reported T_c gold density ≈ 45/47** — far higher than Floquet's
quasienergy track (0/22 literal numbers), because critical temperatures *are*
routinely published as numbers. This is a near-ideal benchmark target.

## QA gauntlet
- **Gold self-verification**: PASS (every gold passes its own verifier).
- **Validator**: PASS (schema, no dup ids, answer-keys≡quantity_ids, no
  model-family split leak).
- **Leak scan**: C1/C2 numeric questions — **0 gold values appear in any
  question** (contrast Floquet's ~45% formula leakage; here golds are
  paper-reported numbers, not formulas an agent could paste). C3 flagged 25
  hits, all verified FALSE POSITIVES (the question lists the allowed label
  set, e.g. "answer one of: first_order/continuous/bkt" — option-listing, not
  answer-stating).
- **Model-family audit**: fixed a canon leak — three records were the pure 2D
  nearest-neighbour square Ising (T_c≈2.269 / K_c=0.4407, the field's most
  famous exact value) under two slugs; re-merged to `ising-nn-square-2d` and
  forced same-split (train). A dipolar-square Ising mis-slugged as plain
  square was separated.
- **Tolerance calibration**: C1/C2 rel_tol set to 2.5× the gold's implied
  sig-fig half-ulp, capped 10%. 17 records adjusted; low-precision golds
  (clock spin glass 0.5, bilayer, some Potts exponents) hit the 10% cap.
- **New verifier**: `categorical_exact` (canonical-label match with an
  aliases map: continuous≡second-order≡2nd-order; bkt≡kosterlitz-thouless)
  added to verify.py and self-tested. This fills the Floquet suite's gap
  (number+formula verified there; this suite adds categorical; code + LLM-
  judge still pending a future build).
- **Independent question-review pass (QA-3, both directions, all 51)**: done
  by two non-author reviewer agents. 8 defects found (~16%, vs Floquet's
  ~45% — numeric/categorical answers don't get pasted like formulas):
  - 2 LEAK: clock-SG stated the A_QQ=0 zero-condition (→T_g=J/2); 2D-EA-SG
    gave "1/nu=0.283 so nu=1/(1/nu)". Both de-leaked (verified by rescan).
  - 2 UNITS: heisenberg-SG-4d `Tc`→`kBTc_over_J`; dipolar-square `h=1`
    defined as stripe period (not a field) + Tc0 units stated.
  - 1 DELETED: 2D-Ising-autoencoder — gold 2.266 is a neural-net-run
    artifact (not model-determined) and duplicates the canonical square
    Ising; dropped (51→50 records).
  - 1 NEW GOLD ERROR (xy-bilayer-cubic-soft): the review + the knowledge-graph service source show
    gold kBTc/Js=2.195 contradicts the paper (reported T1≈0.9, no Binder
    crossing) — flagged needs_original_paper, do not score.
  - C3 fully clean (17/17): categorical questions correctly list the allowed
    label set (option-listing ≠ leak); "foil" mentions (SY conjecture, KPZ
    prediction) are context, not answers.

## Baseline run (partial, 2026-06-13)
a cloud HPC platform sandbox channel validated end-to-end (vectorized 2D Ising MC in a
sandbox reproduced β_c=0.4407 / T_c=2.269 via Binder crossing). A representative
probe was scored before the solver agents were STALL-killed mid-MC (harness
watchdog vs long synchronous sandbox `exec` — see lesson below). Scored 6:

| task | track | result | note |
|---|---|---|---|
| blume-capel-square-d0 | C1 | PASS (1.6935 vs 1.69) | real a cloud HPC platform MC, 0.2% |
| ising-bcc-afm-h0 | C1 | FAIL (4.51 vs 4.11) | **gold-dispute candidate** (J2/J1=1 frustrated; coupling-convention/equilibration — adjudicate) |
| diluted-3potts-sq-p090 | C2 | FAIL | **gold-dispute candidate** (random-fixed-point exponents vs gold's p=0.90 crossover values — adjudicate) |
| 3state-potts-3d-nnn | C3 | PASS (first_order) | recall-solvable |
| mixed-spin-ising-ferrimagnet-sq | C3 | PASS (continuous/2D Ising) | recall-solvable |
| z2-gauge-d4 | C3 | PASS (first_order) | recall-solvable |

Reading: C3 categorical = recall-solvable (low discrimination, like canon
tracks); C1 tractable 2D models solvable via real a cloud HPC platform MC; 2 gold disputes
surfaced for adjudication. No orphaned sandboxes (cost controlled).

**Harness lesson**: long synchronous sandbox `exec` (minutes, no stream
output) gets the solver agent STALL-killed. The full a cloud HPC platform baseline needs the
async pattern — `<cloud-HPC CLI command>` + poll — recorded in the skill.

## Complex-MC retry (2026-06-13) — harness limit confirmed
A second a cloud HPC platform attempt on 4 hard C1 tasks (BCC Ising, 3D Blume-Capel tricritical,
3D ±J spin glass, frustrated XY) with the enhanced env module (compiled-C +
multi-core + async exec) ALSO stalled: the solver agents went silent ~25 min
and were watchdog-killed. The agents repeatedly re-created sandboxes on retry —
6 orphaned sandboxes total across all rounds were hunted from the transcripts
and killed (all confirmed not-found); the multi-core `<machine-sku>` template-create
didn't take, so they fell back to 1-core default (low cost, fully contained).
Confirmed the agents DID use compiled C (`gcc -O3 -march=native`) — so the
stalls are NOT a language/speed issue, definitively the interactive-agent
orchestration pattern. No new results; BCC Ising stays unresolved at 4.51
(vs gold 4.11).

**Finding (eval-harness) — UPDATED:** the stall watchdog was 30 min (1800s);
raising it to **1 h** (settings.json CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS /
CLAUDE_STREAM_IDLE_TIMEOUT_MS) let an agent SUCCEED: group Y completed both hard
tasks (3D ±J spin glass, FFXY) in ~37 min on a cloud HPC platform with compiled-C async MC.
So heavy-MC IS feasible agent-side with **1 h watchdog + async exec+poll +
compiled-C kernel** together — the earlier 30-min stalls were the timeout, not
an impossibility. Caveats still real: agents re-create sandboxes on retry (6
orphans hunted+killed across rounds — and orphan-hunting can kill a *live*
agent's sandbox; group X's BCC/Blume-Capel-tricritical runs were likely
disrupted that way). A batch-job runner remains the cleaner route for a full
scored eval, but the agent route now works for spot baselines.

Hard-task baseline results (group Y, a cloud HPC platform compiled-C):
- 3D ±J Ising spin glass: T_g=1.1057 — matches literature (1.10-1.11) but
  **below gold 1.165 → GOLD DISPUTE** (gold is a high outlier; adjudicate).
- FFXY: T_c=0.446 vs gold 0.403 — agent anchored to pure-FFXY (~0.45) and
  under-captured the NNN shift; legitimate hard FAIL, gold plausibly OK.

## Open queue (before scored use)
- **Heavy-C1 baseline via BATCH JOB, not interactive agent**: submit a
  self-contained `<cloud-HPC CLI command>`
  per task (full MC+FSS solver baked in, runs to completion, writes pred.json),
  then collect — removes the watchdog/orphan problem. Light tasks (2D, C3) are
  already baseline-measured agent-side.
- **Adjudicate** the 2 gold-dispute candidates vs original papers — BCC Ising
  T_N (4.51-vs-4.11: is it under-equilibration or a gold/coupling-convention
  error? a correct batch MC would settle it) and diluted Potts exponents.
- Per-record H(t)-equivalent (model-spec) faithfulness review.
- C2 is `preliminary` (9 < 10).
- The pure 2D square Ising records are canon (T_c=2.269 is universally known)
  — expect them cold-solvable; recorded, not moved (split-integrity principle).

## Provenance
Gold values trace to the knowledge-graph service conclusion nodes (paper_id + verbatim source_excerpt).
Paper pool: atlas `/api/families/10555/papers`. Cluster metadata + skeleton:
`data/workflow_10555.json`. Per-paper classification: `data/` (cls scan).
