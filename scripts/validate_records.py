#!/usr/bin/env python3
"""Validate harbor records: schema completeness + gold self-verification.

Every record's own answer must PASS its verifier (a gold answer that fails
its own tolerance config indicates a malformed record). Also reports split
balance and needs_review counts per track.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verifiers"))
from verify import verify_record  # noqa: E402

REQUIRED_TOP = ["id", "track", "split", "question", "answer", "verifier", "metadata"]
REQUIRED_META = [
    "paper_ref",
    "system",
    "model_family",
    "quantity_ids",
    "gold_provenance",
    "source_ref",
    "source_excerpt",
    "verification_status",
]


def main():
    root = Path(__file__).resolve().parent.parent / "tracks"
    bad = 0
    for jsonl in sorted(root.glob("*/records.jsonl")):
        track = jsonl.parent.name
        records = [json.loads(line) for line in jsonl.read_text().splitlines() if line.strip()]
        splits = Counter(r.get("split") for r in records)
        review = sum(1 for r in records if r["metadata"].get("verification_status") not in ("source_verified", "paper_verified"))
        ids = Counter(r["id"] for r in records)
        for rid, n in ids.items():
            if n > 1:
                print(f"[{track}] duplicate id {rid}")
                bad += 1
        for r in records:
            missing = [k for k in REQUIRED_TOP if k not in r]
            missing += [f"metadata.{k}" for k in REQUIRED_META if k not in r.get("metadata", {})]
            if missing:
                print(f"[{track}] {r.get('id','?')}: missing {missing}")
                bad += 1
                continue
            if not r["answer"]:
                print(f"[{track}] {r['id']}: empty answer")
                bad += 1
                continue
            if sorted(r["answer"]) != sorted(r["metadata"]["quantity_ids"]):
                print(f"[{track}] {r['id']}: answer keys != quantity_ids")
                bad += 1
            failures, _ = verify_record(r, r["answer"])
            if failures:
                print(f"[{track}] {r['id']}: gold fails own verifier: {failures}")
                bad += 1
        fams_train = {r["metadata"]["model_family"] for r in records if r["split"] == "train"}
        fams_val = {r["metadata"]["model_family"] for r in records if r["split"] == "validation"}
        leak = fams_train & fams_val
        if leak:
            print(f"[{track}] model-family leak across splits: {sorted(leak)}")
            bad += 1
        print(
            f"[{track}] {len(records)} records "
            f"(train {splits.get('train',0)} / validation {splits.get('validation',0)}), "
            f"{review} needing original-paper review"
        )
    if bad:
        print(f"FAIL: {bad} problems")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
