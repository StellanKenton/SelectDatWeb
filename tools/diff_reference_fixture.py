from __future__ import annotations

import json
from pathlib import Path

from core.shanjia import calculate_days


FIXTURE = Path("reference_fixtures/shanjia_2026_dingyou_ren.json")


def lesson_pairs(level: str, common: dict) -> list[str]:
    payload = dict(common)
    payload.update(
        {
            "start_date": "2026-01-15",
            "end_date": "2027-02-15",
            "level": level,
        }
    )
    result = calculate_days(payload)
    return [f"{item['date']}T{int(item['hour']):02d}" for item in result["results"]]


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    common = fixture["input"]
    report = {}
    for level, expected in fixture["levels"].items():
        got = lesson_pairs(level, common)
        exp_set, got_set = set(expected["pairs"]), set(got)
        report[level] = {
            "reference_count": expected["count"],
            "local_count": len(got),
            "missing_count": len(exp_set - got_set),
            "extra_count": len(got_set - exp_set),
            "missing": sorted(exp_set - got_set),
            "extra": sorted(got_set - exp_set),
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    Path("reference_fixtures/latest_diff.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
