from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("main_src").resolve()))
from core import calculate_days  # noqa: E402

EXPECTED = {"全部": 78, "大吉": 0, "小吉": 0, "生旺": 42, "耗": 9}


def count(level: str) -> int:
    result = calculate_days(
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
    return result["count"]


def main() -> int:
    got = {level: count(level) for level in EXPECTED}
    report = {
        level: {
            "reference": EXPECTED[level],
            "local": got[level],
            "delta": got[level] - EXPECTED[level],
        }
        for level in EXPECTED
    }
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
