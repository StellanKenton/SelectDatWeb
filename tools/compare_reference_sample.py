from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import calculate_days


def latest_reference_html() -> Path:
    files = sorted(Path("reference_capture").glob("*/zeri.html"))
    if not files:
        raise RuntimeError("没有 reference_capture/*/zeri.html")
    return files[-1]


def main() -> int:
    html_path = latest_reference_html()
    html = html_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"显示：\s*(\d+)个日课", html)
    reference_count = int(m.group(1)) if m else -1

    payload = {
        "start_date": "2026-09-28",
        "end_date": "2026-09-28",
        "use_type": "建造",
        "mountain_id": 1,
        "jian": "亥巳",
        "fenjin": "乙亥",
        "dagua": "风地观",
        "dagua_value": "2;2",
        "life_years": [],
        "favorable_months": [],
        "level": "全部",
        "hours": [0],
    }
    local = calculate_days(payload)

    report = {
        "reference_initial_count": reference_count,
        "reference_contains_2026_09_28": "9月28日" in html,
        "local_count": local["count"],
        "local_results": [
            {
                "date": x["date"],
                "day_ganzhi": x["day_ganzhi"],
                "month_ganzhi": x["month_ganzhi"],
                "score": x["score"],
                "level": x["level_name"],
                "relation": x["relation"],
                "good": x["good"],
                "bad": x["bad"],
            }
            for x in local["results"]
        ],
    }
    Path("reference_compare").mkdir(exist_ok=True)
    Path("reference_compare/default_sample.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
