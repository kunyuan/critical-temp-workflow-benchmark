# Critical-Temperature Workflow Benchmark

A harbor-format benchmark testing whether an agent can **reproduce and apply
the Monte Carlo finite-size-scaling workflow for classical-lattice critical
temperatures** (workflow family #10555: define a classical spin model → Monte
Carlo sampling → thermodynamic observables → locate finite-size critical
points → finite-size extrapolation → report critical parameters), built from
the published literature of that family.

## Structure: three tracks, typed verifiers

Each record in a track exercises the same workflow facet; answers are numbers
or categorical labels, each with a typed verifier.

| Track | Facet | Answer type | Verifier |
|---|---|---|---|
| `C1-critical-point` ★ | **flagship: the full MC+FSS loop → T_c / K_c** | numeric | `scalar_tolerance` |
| `C2-critical-exponents` | FSS collapse → ν, γ/ν, β/ν, η, z | numeric | `scalar_tolerance` |
| `C3-transition-character` | order (first/continuous/BKT) + universality class | categorical | `categorical_exact` |

C1 is the end-to-end metric (it includes the finite-size-extrapolation outer
loop); C2/C3 decompose the capability. Every track ships a **train** split
(worked examples for skill distillation) and a question-only **validation**
split, stratified by model family.

## Layout

```
data/workflow_preamble.md    # shared workflow description (Q module 1)
data/environment_setup.md    # shared environment & answer protocol (Q module 2)
tracks/<track>/records.jsonl # canonical records (per-paper Q + answer + verifier + provenance)
tasks/<track>/<id>/          # materialized harbor tasks (instruction.md = assembled prompt)
verifiers/verify.py          # typed verifiers (scalar / integer / set / formula sampling / categorical)
scripts/                     # assemble_prompt, materialize_harbor, splits, validation, scoring
```

Prompts are assembled deterministically (`scripts/assemble_prompt.py`);
`records.jsonl` is the single source of truth.

## Verification

```bash
python verifiers/verify.py --record <record.json> --pred <pred.json>
python scripts/validate_records.py    # schema + gold self-check + split-leak check
python scripts/score_run.py <run_dir> # score a solve run, per track × split
```

The `categorical_exact` verifier matches transition-order / universality-class
labels after canonicalization with an aliases map (continuous ≡ second-order;
bkt ≡ Kosterlitz-Thouless). Numeric tolerances are calibrated to each gold's
significant figures.

## Provenance & honest state

Gold values trace to published papers; records carry a verbatim source excerpt
and opaque provenance refs (`paper_ref` / `source_ref`). Records flagged
`needs_original_paper` await verification against the original publication and
are excluded from scored use — see `quality_report.md` for the full QA history,
the four gold disputes surfaced by the baseline run + independent review, and
per-item difficulty metadata. The benchmark passed a two-direction independent
question review (leak + completeness); compute-heavy C1 tasks assume access to
a cloud HPC sandbox (declared in the environment module).

## Status

50 records (C1 24 / C2 9 / C3 17; C2 is *preliminary*, below the sizing floor).
4 records are `needs_original_paper` (gold disputes pending adjudication).
