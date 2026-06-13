#!/usr/bin/env python3
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
