#!/usr/bin/env python3
"""Materialize harbor task directories from canonical records.jsonl.

Every record — regardless of verifier type (number / formula / code /
llm_judge) — becomes a standard harbor task:

    tasks/<track>/<record_id>/
      task.toml          # metadata + verifier config + split
      instruction.md     # the question (all the agent sees)
      tests/
        record.json      # full record (held by harness; contains gold)
        score.py         # shim -> shared verifiers/verify.py
      environment/packet/  # (code-type tasks only: dev cases + dev gold)

records.jsonl stays the single source of truth; this script is deterministic
and idempotent — rerun after any record edit.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"

sys.path.insert(0, str(ROOT / "scripts"))
from assemble_prompt import assemble  # noqa: E402

SCORE_SHIM = '''#!/usr/bin/env python3
"""Harbor scorer shim: compares pred.json against this task's gold."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "verifiers"))
from verify import verify_record  # noqa: E402


def main():
    pred_path = sys.argv[sys.argv.index("--pred") + 1] if "--pred" in sys.argv else "pred.json"
    record = json.loads((HERE / "record.json").read_text())
    pred = json.loads(Path(pred_path).read_text())
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
'''


def toml_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def emit_task(record):
    track = {"C1": "C1-critical-point", "C2": "C2-critical-exponents",
             "C3": "C3-transition-character"}[record["track"]]
    tdir = TASKS / track / record["id"]
    tdir.mkdir(parents=True, exist_ok=True)
    m = record["metadata"]
    v = record["verifier"]
    lines = [
        'version = "1.0"',
        "",
        "[metadata]",
        f'id = "{record["id"]}"',
        f'track = "{record["track"]}"',
        f'split = "{record["split"]}"',
        f'paper_ref = "{m["paper_ref"]}"',
        f'system = "{toml_escape(m["system"])}"',
        f'model_family = "{m["model_family"]}"',
        f'gold_provenance = "{m["gold_provenance"]}"',
        f'verification_status = "{m["verification_status"]}"',
        f'quantity_ids = {json.dumps(m["quantity_ids"])}',
        "",
        "[verifier]",
        f'type = "{v["type"]}"',
    ]
    for key, val in v.items():
        if key == "type":
            continue
        lines.append(f"{key} = {json.dumps(val)}")
    lines += [
        'scorer = "python tests/score.py --pred pred.json"',
        "timeout_sec = 120.0",
        "",
        "[agent]",
        "timeout_sec = 3600.0",
    ]
    (tdir / "task.toml").write_text("\n".join(lines) + "\n")
    (tdir / "instruction.md").write_text(assemble(record))
    tests = tdir / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "record.json").write_text(json.dumps(record, indent=1, ensure_ascii=False))
    (tests / "score.py").write_text(SCORE_SHIM)
    return tdir


def main():
    if TASKS.exists():
        shutil.rmtree(TASKS)
    count = 0
    for jsonl in sorted((ROOT / "tracks").glob("*/records.jsonl")):
        for line in jsonl.read_text().splitlines():
            if line.strip():
                emit_task(json.loads(line))
                count += 1
    print(f"materialized {count} harbor tasks under {TASKS}")


if __name__ == "__main__":
    main()
