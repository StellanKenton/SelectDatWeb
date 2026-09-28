from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MAIN_SRC = Path("main_src").resolve()
sys.path.insert(0, str(MAIN_SRC))

from core import calculate_days  # noqa: E402


LEVEL_FILES = {
    "全部": "all",
    "大吉": "daji",
    "小吉": "xiaoji",
    "生旺": "shengwang",
    "耗": "hao",
}


def reference_pairs(path: Path) -> list[tuple[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    blocks = text.split("[打印] ")[1:]
    pairs: list[tuple[str, int]] = []
    for block in blocks:
        date_m = re.search(r"公历:(\d+)月(\d+)日", block)
        hour_m = re.search(r"\n(\d+)点\n", block)
        if not date_m or not hour_m:
            continue
        date = f"2026-{int(date_m.group(1)):02d}-{int(date_m.group(2)):02d}"
        pairs.append((date, int(hour_m.group(1))))
    return pairs


def local(level: str) -> list[tuple[str, int]]:
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
            "hours": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
        }
    )
    return [(item["date"], int(item["hour"])) for item in result["results"]]


def main() -> int:
    report = {}
    for level, safe in LEVEL_FILES.items():
        ref = reference_pairs(Path("reference_browser") / f"center_result_{safe}.txt")
        got = local(level)
        ref_set, got_set = set(ref), set(got)
        report[level] = {
            "reference_count": len(ref),
            "local_count": len(got),
            "missing_count": len(ref_set - got_set),
            "extra_count": len(got_set - ref_set),
            "missing": sorted(ref_set - got_set)[:30],
            "extra": sorted(got_set - ref_set)[:30],
        }
    Path("reference_compare").mkdir(exist_ok=True)
    Path("reference_compare/level_diff.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
