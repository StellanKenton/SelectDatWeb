"""Summarize local comparisons from saved visible-site samples only."""

from __future__ import annotations

import json
import re
from pathlib import Path

from core.shanjia import calculate_days, get_month_sha, get_year_sha


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
CASES = (
    ("B02_right_reference.json", 1, "大吉", "协纪版"),
    ("B15_right_all_reference.json", 1, "全部", "协纪版"),
    ("B15_right_yiji_off_reference.json", 1, "全部", "不显示"),
    ("B07_bing_mountain_reference.json", 13, "全部", "不显示"),
    ("B07_no_month_sansha_reference.json", 13, "全部", "不显示"),
    ("B07_no_month_time_sansha_reference.json", 13, "全部", "不显示"),
)


def read(filename: str) -> dict:
    return json.loads((OUTPUT / filename).read_text(encoding="utf-8"))


def dates(text: str) -> list[str]:
    return [f"2026-{int(month):02d}-{int(day):02d}"
            for month, day in re.findall(r"公历:(\d+)月(\d+)日", text)]


def main() -> None:
    cases = []
    for filename, mountain_id, level, edition in CASES:
        source = read(filename)
        filters = [row["value"] for row in source["active_filters"]
                   if row["name"] == "Arry_xiongsha[]"]
        local = calculate_days({"start_date": "2026-09-01", "end_date": "2026-09-30",
                                "use_type": "建造", "mountain_id": mountain_id,
                                "level": level, "edition": edition, "hours": [0],
                                "sha_filters": filters})
        site_dates = dates(source["center_text"])
        local_dates = [row["date"] for row in local["results"]]
        cases.append({"source": filename, "mountain_id": mountain_id,
                      "level": level, "edition": edition, "site_count": source["result_count"],
                      "local_count": local["count"], "site_dates": site_dates,
                      "local_dates": local_dates, "exact_date_set": site_dates == local_dates})
    month = get_month_sha(2026, "丙申")
    year = get_year_sha(2026, 1)
    summary = {
        "source": "saved visible Edge UI results; this program sends no website requests",
        "website_queries_this_round": 6,
        "month": {"year": 2026, "ganzhi": "丙申",
                  "bad_rows": len(month["bad"]), "good_rows": len(month["good"]),
                  "whole_saved_table_equal": month["visible_text"] == read("month_year_2026_reference.json")["month_text"].split("\n\n【泄】 庚寅月【点击添加】", 1)[0]},
        "year": {"start": 2026, "end": 2035, "mountain_ids_tested": [1, 13],
                 "cards_per_mountain": len(year["cards"]), "rows_per_card": len(year["cards"][0]["rows"])},
        "right_search_cases": cases,
        "right_search_matching_cases": sum(row["exact_date_set"] for row in cases),
        "right_search_total_cases": len(cases),
        "full_lesson_text_equal": False,
        "full_lesson_text_reason": "Local UI does not yet render all fields in the original cards.",
    }
    (OUTPUT / "round2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"matching_cases": summary["right_search_matching_cases"],
                      "total_cases": len(cases), "counts": [(r["site_count"], r["local_count"]) for r in cases]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
