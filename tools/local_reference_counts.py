from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("main_src").resolve()))
from core import calculate_days  # noqa: E402

EXPECTED_COUNTS = {"全部": 78, "大吉": 0, "小吉": 0, "生旺": 42, "耗": 9}

REFERENCE_ALL = {
    "2026-09-08T00","2026-09-08T02","2026-09-08T06","2026-09-08T08","2026-09-08T10","2026-09-08T14","2026-09-08T16","2026-09-08T18","2026-09-08T22",
    "2026-09-10T00","2026-09-10T02","2026-09-10T06","2026-09-10T08","2026-09-10T10","2026-09-10T14","2026-09-10T16","2026-09-10T18","2026-09-10T22",
    "2026-09-15T00","2026-09-15T02","2026-09-15T06","2026-09-15T08","2026-09-15T10","2026-09-15T14","2026-09-15T16","2026-09-15T18","2026-09-15T22",
    "2026-09-16T00","2026-09-16T02","2026-09-16T06","2026-09-16T08","2026-09-16T10","2026-09-16T16","2026-09-16T18","2026-09-16T22",
    "2026-09-18T00","2026-09-18T02","2026-09-18T06","2026-09-18T08","2026-09-18T10","2026-09-18T14","2026-09-18T16","2026-09-18T18","2026-09-18T22",
    "2026-09-23T00","2026-09-23T02","2026-09-23T06","2026-09-23T08","2026-09-23T10","2026-09-23T14","2026-09-23T16","2026-09-23T18","2026-09-23T22",
    "2026-09-28T00","2026-09-28T02","2026-09-28T06","2026-09-28T08","2026-09-28T10","2026-09-28T14","2026-09-28T16","2026-09-28T18","2026-09-28T22",
    "2026-10-04T00","2026-10-04T06","2026-10-04T08","2026-10-04T10","2026-10-04T14","2026-10-04T16","2026-10-04T18","2026-10-04T22",
    "2026-10-06T00","2026-10-06T02","2026-10-06T06","2026-10-06T08","2026-10-06T10","2026-10-06T16","2026-10-06T18","2026-10-06T22",
}


def calculate(level: str) -> dict:
    return calculate_days(
        {
            "start_date": "2026-01-15",
            "end_date": "2027-02-15",
            "ganzhi_year": "丙午",
            "ganzhi_month": "丁酉",
            "ganzhi_day_filter": "全部",
            "use_type": "建造",
            "edition": "协纪版",
            "mountain_id": 1,
            "jian": "亥巳",
            "fenjin": "乙亥",
            "dagua": "风地观",
            "dagua_value": "2;2",
            "life_years": [],
            "favorable_months": [],
            "level": level,
            "hours": [0,2,4,6,8,10,12,14,16,18,20,22],
        }
    )


def pair_set(result: dict) -> set[str]:
    return {f"{row['date']}T{int(row['hour']):02d}" for row in result["results"]}


def main() -> int:
    results = {level: calculate(level) for level in EXPECTED_COUNTS}
    report = {
        level: {
            "reference": EXPECTED_COUNTS[level],
            "local": results[level]["count"],
            "delta": results[level]["count"] - EXPECTED_COUNTS[level],
        }
        for level in EXPECTED_COUNTS
    }
    got_all = pair_set(results["全部"])
    report["全部"]["missing_count"] = len(REFERENCE_ALL - got_all)
    report["全部"]["extra_count"] = len(got_all - REFERENCE_ALL)
    report["全部"]["missing"] = sorted(REFERENCE_ALL - got_all)
    report["全部"]["extra"] = sorted(got_all - REFERENCE_ALL)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
