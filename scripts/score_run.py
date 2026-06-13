#!/usr/bin/env python3
"""Score a solve run: predictions under <run_dir>/<record_id>/pred.json are
verified against each record's gold; aggregates per track x split.

Usage: python scripts/score_run.py /tmp/asb_eval
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "verifiers"))
from verify import verify_record  # noqa: E402


def main():
    run_dir = Path(sys.argv[1])
    agg = defaultdict(lambda: [0, 0])
    rows = []
    for jsonl in sorted((ROOT / "tracks").glob("*/records.jsonl")):
        track = jsonl.parent.name
        for line in jsonl.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            pred_path = run_dir / r["id"] / "pred.json"
            key = (track, r["split"])
            agg[key][1] += 1
            if not pred_path.exists():
                rows.append((track, r["split"], r["id"], "NO_PRED", ""))
                continue
            try:
                pred = json.loads(pred_path.read_text())
                failures, details = verify_record(r, pred)
            except Exception as exc:
                rows.append((track, r["split"], r["id"], "ERROR", str(exc)[:60]))
                continue
            ok = not failures
            agg[key][0] += ok
            err = ""
            if details:
                try:
                    errs = [d[3] for d in details if isinstance(d[3], (int, float))]
                    if errs:
                        err = f"max_err={max(errs):.3g}"
                except Exception:
                    pass
            rows.append((track, r["split"], r["id"], "PASS" if ok else "FAIL", err))
    for row in rows:
        print(f"{row[0]:24s} {row[1]:10s} {row[2]:46s} {row[3]:7s} {row[4]}")
    print("\n=== per track x split ===")
    for (track, split), (p, t) in sorted(agg.items()):
        print(f"{track:24s} {split:10s} {p}/{t} passed")


if __name__ == "__main__":
    main()
