#!/usr/bin/env python3
"""Deterministic Q assembly: module 1 (workflow preamble) + module 2
(environment setup, optional) + module 3 (per-paper question).

Single source of truth for what an agent sees. The harbor materializer and
any probe/eval launcher must both call assemble() — never concatenate by
hand.

CLI:
  python assemble_prompt.py <record_id>          # print assembled prompt
  python assemble_prompt.py --all --out DIR      # one .md per record
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_records():
    out = {}
    for jsonl in sorted((ROOT / "tracks").glob("*/records.jsonl")):
        for line in jsonl.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r
    return out


def assemble(record):
    parts = [(ROOT / "data" / "workflow_preamble.md").read_text()]
    env = ROOT / "data" / "environment_setup.md"
    if env.exists() and record.get("metadata", {}).get("include_env_module", True):
        parts.append(env.read_text())
    parts.append(record["question"] + "\n")
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("record_id", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()
    records = load_records()
    if args.all:
        outdir = Path(args.out or "/tmp/assembled_prompts")
        outdir.mkdir(parents=True, exist_ok=True)
        for rid, r in records.items():
            (outdir / f"{rid}.md").write_text(assemble(r))
        print(f"wrote {len(records)} prompts to {outdir}")
    elif args.record_id:
        if args.record_id not in records:
            sys.exit(f"unknown record id: {args.record_id}")
        print(assemble(records[args.record_id]), end="")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
