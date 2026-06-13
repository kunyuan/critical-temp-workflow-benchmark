#!/usr/bin/env python3
"""Shared harbor verifiers for the Floquet workflow benchmark suite.

One verifier type per track; a record's ``verifier`` block selects the type
and per-record overrides. The agent-facing contract: predictions are a JSON
object mapping quantity_id -> value, compared against the record's ``answer``.

Verifier types:
  integer_exact      (B1) canonical integers, exact equality per field.
  quasienergy_set    (B2) dimensionless quasienergies folded to (-1/2, 1/2],
                          sorted pairwise match under relative tolerance.
                          Named scalar fields are also supported (gaps etc.).
  scalar_tolerance   (B3/B4) named float scalars under relative tolerance,
                          default chosen by gold provenance.

CLI:
  python verify.py --record path/to/record.json --pred path/to/pred.json
exits 0 on PASS, 1 on FAIL, prints per-field diagnostics either way.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

DEFAULT_REL_TOL = {
    "formula_derived": 1e-3,
    "reference_solver": 1e-4,
    "paper_reported_numeric": 1e-3,
    "figure_derived": 0.05,
}


def _canonical_int(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field}: booleans are not integers")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    raise ValueError(f"{field}: non-canonical integer {value!r}")


def _as_float(value, field):
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}: not a number: {value!r}") from exc
    if not math.isfinite(out):
        raise ValueError(f"{field}: non-finite value")
    return out


def _rel_err(got, ref):
    if ref == 0.0:
        return abs(got)
    return abs(got - ref) / abs(ref)


def _fold(x):
    """Fold a dimensionless quasienergy into (-1/2, 1/2]."""
    y = x - math.floor(x + 0.5)
    if y <= -0.5:
        y += 1.0
    return y


def verify_integer_exact(pred, answer, config):
    failures, details = [], []
    for field, ref in answer.items():
        if field not in pred:
            failures.append((field, "missing", None, ref))
            continue
        try:
            got = _canonical_int(pred[field], field)
        except ValueError as exc:
            failures.append((field, str(exc), pred[field], ref))
            continue
        details.append((field, got, ref, 0 if got == ref else 1))
        if got != ref:
            failures.append((field, "mismatch", got, ref))
    return failures, details


def verify_scalar_tolerance(pred, answer, config):
    provenance = config.get("gold_provenance", "paper_reported_numeric")
    default_tol = config.get("rel_tol") or DEFAULT_REL_TOL.get(provenance, 1e-3)
    per_field = config.get("per_field_rel_tol", {})
    failures, details = [], []
    for field, ref in answer.items():
        tol = per_field.get(field, default_tol)
        if field not in pred:
            failures.append((field, "missing", None, ref))
            continue
        try:
            got = _as_float(pred[field], field)
        except ValueError as exc:
            failures.append((field, str(exc), pred[field], ref))
            continue
        err = _rel_err(got, _as_float(ref, field))
        details.append((field, got, ref, err))
        if err > tol:
            failures.append((field, f"rel_err {err:.3g} > tol {tol:.3g}", got, ref))
    return failures, details


def verify_quasienergy_set(pred, answer, config):
    tol = config.get("rel_tol", 1e-4)
    abs_tol = config.get("abs_tol", 1e-6)
    failures, details = [], []
    scalar_answer = {k: v for k, v in answer.items() if not isinstance(v, list)}
    if scalar_answer:
        f, d = verify_scalar_tolerance(pred, scalar_answer, config)
        failures += f
        details += d
    for field, ref in answer.items():
        if not isinstance(ref, list):
            continue
        if field not in pred or not isinstance(pred[field], list):
            failures.append((field, "missing or not a list", None, ref))
            continue
        got = sorted(_fold(_as_float(x, field)) for x in pred[field])
        want = sorted(_fold(_as_float(x, field)) for x in ref)
        if len(got) != len(want):
            failures.append((field, f"count {len(got)} != {len(want)}", got, want))
            continue
        worst = 0.0
        for g, w in zip(got, want):
            err = abs(g - w) if abs(w) < abs_tol else _rel_err(g, w)
            worst = max(worst, err)
        details.append((field, got, want, worst))
        if worst > tol:
            failures.append((field, f"worst err {worst:.3g} > tol {tol:.3g}", got, want))
    return failures, details


def _caret_to_pow(expr):
    """Replace `^` (math exponentiation convention) with Python `**`.
    Leaves existing `**` intact. Caret-as-XOR has no legitimate use in these
    numeric physics formulas, so the substitution is unambiguous."""
    return expr.replace("**", "\x00").replace("^", "**").replace("\x00", "**")


def _csqrt(x):
    """sqrt that follows arguments into the complex plane (1j literals are
    allowed in expressions, so negative/complex radicands must work)."""
    import numpy as np
    arr = np.asarray(x)
    if np.iscomplexobj(arr) or np.any(np.asarray(np.real(arr) != arr, dtype=bool)):
        return np.sqrt(arr.astype(complex))
    if np.any(arr < 0):
        return np.sqrt(arr.astype(complex))
    return np.sqrt(arr)


def verify_formula_equivalence(pred, answer, config):
    """Answer type 'formula': pred fields are python-evaluable expression strings
    in the declared variables; gold is the reference expression. Equivalence is
    checked by sampling: both expressions are evaluated at config['samples']
    points drawn from config['variables'] ranges and compared under rel_tol.

    config example:
      {"variables": {"beta": [0.1, 2.0], "omega": [0.5, 5.0]},
       "samples": 32, "rel_tol": 1e-6}
    Allowed names inside expressions: the declared variables plus math/numpy
    functions (sin, cos, exp, sqrt, pi, ...) and scipy.special Bessel functions
    (j0, j1, jv).
    """
    import numpy as np
    from scipy import special

    rng = np.random.default_rng(config.get("seed", 20260612))
    variables = config["variables"]
    n = config.get("samples", 32)
    tol = config.get("rel_tol", 1e-6)

    def _fold(x):
        """Fold a dimensionless quasienergy into (-1/2, 1/2]."""
        y = np.asarray(x) - np.floor(np.asarray(x) + 0.5)
        return np.where(y <= -0.5, y + 1.0, y)

    def _summ(f, lo, hi):
        """Finite series sum: summ(lambda m: ..., lo, hi), inclusive."""
        return sum(f(m) for m in range(int(lo), int(hi) + 1))

    env_base = {
        "sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp,
        "sqrt": _csqrt, "log": np.log, "abs": np.abs, "pi": np.pi,
        "arccos": np.arccos, "arcsin": np.arcsin, "arctan": np.arctan,
        "cosh": np.cosh, "sinh": np.sinh, "tanh": np.tanh,
        "j0": special.j0, "j1": special.j1, "jv": special.jv,
        "re": np.real, "im": np.imag, "conj": np.conj,
        "fold": _fold, "floor": np.floor, "summ": _summ,
    }
    failures, details = [], []
    points = {v: rng.uniform(lo, hi, n) for v, (lo, hi) in variables.items()}
    for field, ref_expr in answer.items():
        if field not in pred:
            failures.append((field, "missing", None, ref_expr))
            continue
        got_expr = pred[field]
        if not isinstance(got_expr, str):
            failures.append((field, "formula answer must be an expression string", got_expr, ref_expr))
            continue
        try:
            # env goes in globals (not locals) so lambda bodies inside summ()
            # can resolve names like jv at call time
            scope = {"__builtins__": {}, **env_base, **points}
            # normalize caret (math power convention) to Python's ** — agents
            # routinely write ^ for exponentiation; Python would read it as XOR
            ref_vals = eval(_caret_to_pow(ref_expr), scope, {})
            got_vals = eval(_caret_to_pow(got_expr), scope, {})
        except Exception as exc:
            failures.append((field, f"evaluation error: {exc}", got_expr, ref_expr))
            continue
        ref_vals = np.broadcast_to(np.asarray(ref_vals, dtype=complex), (n,))
        got_vals = np.broadcast_to(np.asarray(got_vals, dtype=complex), (n,))
        denom = np.maximum(np.abs(ref_vals), 1e-12)
        worst = float(np.max(np.abs(got_vals - ref_vals) / denom))
        details.append((field, got_expr, ref_expr, worst))
        if not math.isfinite(worst) or worst > tol:
            failures.append((field, f"max sampled rel_err {worst:.3g} > tol {tol:.3g}", got_expr, ref_expr))
    return failures, details


def _canon_label(s):
    return str(s).strip().lower().replace(" ", "").replace("-", "").replace("_", "").replace("/", "")


def verify_categorical_exact(pred, answer, config):
    """Categorical answers (transition order, universality class): exact match
    after canonicalization. Optional config['aliases'] = {field: {canonical:
    [synonyms]}} so 'continuous' == 'second order' == '2nd-order'."""
    aliases = config.get("aliases", {})
    failures, details = [], []
    for field, ref in answer.items():
        if field not in pred:
            failures.append((field, "missing", None, ref))
            continue
        got, want = _canon_label(pred[field]), _canon_label(ref)
        amap = aliases.get(field, {})
        groups = [{_canon_label(can)} | {_canon_label(s) for s in syns} for can, syns in amap.items()]
        same = got == want or any(got in g and want in g for g in groups)
        details.append((field, pred[field], ref, 0 if same else 1))
        if not same:
            failures.append((field, "label mismatch", pred[field], ref))
    return failures, details


VERIFIERS = {
    "integer_exact": verify_integer_exact,
    "quasienergy_set": verify_quasienergy_set,
    "scalar_tolerance": verify_scalar_tolerance,
    "formula_equivalence": verify_formula_equivalence,
    "categorical_exact": verify_categorical_exact,
}


def verify_record(record, pred):
    vconf = record["verifier"]
    fn = VERIFIERS[vconf["type"]]
    config = dict(vconf)
    config.setdefault("gold_provenance", record.get("metadata", {}).get("gold_provenance"))
    failures, details = fn(pred, record["answer"], config)
    extra = sorted(set(pred) - set(record["answer"]))
    if extra:
        failures.append(("_extra_fields", f"unexpected fields {extra}", None, None))
    return failures, details


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", required=True)
    parser.add_argument("--pred", required=True)
    args = parser.parse_args()
    record = json.load(open(args.record))
    pred = json.load(open(args.pred))
    failures, details = verify_record(record, pred)
    for field, got, ref, err in details:
        print(f"  {field}: got={got} ref={ref} err={err}")
    if failures:
        print("FAIL")
        for field, why, got, ref in failures:
            print(f"  {field}: {why} (got={got} ref={ref})")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
