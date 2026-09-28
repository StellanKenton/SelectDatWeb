from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from core.shanjia import calculate_days


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def by_date(rows: list[dict]) -> dict[str, dict]:
    return {str(row["date"]): row for row in rows}


def normalize_hours(row: dict) -> set[str]:
    raw = row.get("hours", [])
    result: set[str] = set()
    for item in raw:
        if isinstance(item, dict):
            if item.get("ganzhi"):
                result.add(str(item["ganzhi"]))
            elif item.get("zhi"):
                result.add(str(item["zhi"]))
        else:
            result.add(str(item))
    return result


def compare_case(case: dict) -> dict:
    local = calculate_days(case["input"])
    reference_rows = case.get("reference", [])
    local_map = by_date(local["results"])
    ref_map = by_date(reference_rows)

    local_dates = set(local_map)
    ref_dates = set(ref_map)

    missing = sorted(ref_dates - local_dates)
    extra = sorted(local_dates - ref_dates)
    common = sorted(ref_dates & local_dates)

    level_mismatch = []
    hour_mismatch = []
    for day in common:
        expected = ref_map[day]
        actual = local_map[day]

        expected_level = expected.get("level_name") or expected.get("level")
        actual_level = actual.get("level_name") or actual.get("level")
        if expected_level is not None and str(expected_level) != str(actual_level):
            level_mismatch.append(
                {
                    "date": day,
                    "reference": expected_level,
                    "local": actual_level,
                }
            )

        expected_hours = normalize_hours(expected)
        if expected_hours:
            actual_hours = normalize_hours(actual)
            if expected_hours != actual_hours:
                hour_mismatch.append(
                    {
                        "date": day,
                        "reference": sorted(expected_hours),
                        "local": sorted(actual_hours),
                    }
                )

    return {
        "case_id": case.get("case_id", ""),
        "reference_count": len(ref_dates),
        "local_count": len(local_dates),
        "missing_dates": missing,
        "extra_dates": extra,
        "level_mismatch": level_mismatch,
        "hour_mismatch": hour_mismatch,
        "matched_dates": len(common),
        "exact_date_match": not missing and not extra,
        "exact_match": not missing and not extra and not level_mismatch and not hour_mismatch,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare local shanjia output with normalized reference fixtures.")
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = load_json(args.fixture)
    cases = payload if isinstance(payload, list) else payload.get("cases", [])
    results = [compare_case(case) for case in cases]

    report = {
        "cases": results,
        "exact_cases": sum(1 for item in results if item["exact_match"]),
        "total_cases": len(results),
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if all(item["exact_match"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
