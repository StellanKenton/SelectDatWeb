from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("main_src").resolve()))
import core.shanjia as sj  # noqa: E402


PAYLOAD = {
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
    "level": "全部",
    "hours": [0,2,4,6,8,10,12,14,16,18,20,22],
}


def ids(result: dict) -> set[str]:
    return {str(row["lesson_id"]) for row in result["results"]}


def main() -> int:
    original = tuple(sj.REFERENCE_SHA_FILTERS["建造"])
    baseline = sj.calculate_days(dict(PAYLOAD))
    base_ids = ids(baseline)
    report = {
        "baseline_count": baseline["count"],
        "leave_one_out": {},
    }
    try:
        for rule in original:
            sj.REFERENCE_SHA_FILTERS["建造"] = tuple(x for x in original if x != rule)
            result = sj.calculate_days(dict(PAYLOAD))
            current = ids(result)
            report["leave_one_out"][rule] = {
                "count": result["count"],
                "restored_count": len(current - base_ids),
                "restored_ids": sorted(current - base_ids),
                "removed_count": len(base_ids - current),
                "removed_ids": sorted(base_ids - current),
            }
    finally:
        sj.REFERENCE_SHA_FILTERS["建造"] = original
    print(json.dumps(report, ensure_ascii=False))
    Path("reference_isolation").mkdir(exist_ok=True)
    Path("reference_isolation/local_ablation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
