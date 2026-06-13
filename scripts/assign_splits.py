#!/usr/bin/env python3
"""Assign train/validation splits, stratified by model_family.

Whole model families go to one side (anti-leak: a validation paper must not
share a model family with any train paper). Families are ordered
deterministically by (size desc, name) and greedily assigned to keep the
train share near TRAIN_FRACTION, largest families to train first so the
worked-example pool covers the most common model classes.

Usage: python assign_splits.py            # rewrite records.jsonl per track
       python assign_splits.py --dry-run  # print the assignment only
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

TRAIN_FRACTION = 0.55


def assign(records):
    families = defaultdict(list)
    for r in records:
        families[r["metadata"]["model_family"]].append(r)
    ordered = sorted(families.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    total = len(records)
    train_n = 0
    plan = {}
    for fam, members in ordered:
        side = "train" if train_n + len(members) <= max(1, round(total * TRAIN_FRACTION)) else "validation"
        if side == "train":
            train_n += len(members)
        plan[fam] = side
    if train_n == 0 and ordered:
        plan[ordered[0][0]] = "train"
    for r in records:
        r["split"] = plan[r["metadata"]["model_family"]]
    return plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent / "tracks"
    for draft in sorted(root.glob("*/records_draft.jsonl")):
        records = [json.loads(line) for line in draft.read_text().splitlines() if line.strip()]
        plan = assign(records)
        counts = {"train": 0, "validation": 0}
        for r in records:
            counts[r["split"]] += 1
        print(f"[{draft.parent.name}] {counts['train']} train / {counts['validation']} validation")
        for fam, side in sorted(plan.items()):
            n = sum(1 for r in records if r["metadata"]["model_family"] == fam)
            print(f"    {fam:30s} -> {side} ({n})")
        if not args.dry_run:
            out = draft.parent / "records.jsonl"
            out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
            print(f"    wrote {out}")


if __name__ == "__main__":
    main()
