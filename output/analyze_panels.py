"""Compare one UI capture of the month and year panes with local rule tables."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from core.shanjia import get_year_sha  # noqa: E402


def parse_year_cards(text: str) -> list[dict]:
    starts = list(re.finditer(r"(?m)^([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])年凶煞【点击选择】(大利|不利)$", text))
    cards = []
    for index, hit in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[hit.end():end].split("【点击展开凶煞】", 1)[0]
        rows = [tuple(match.groups()) for match in re.finditer(r"(?m)^【([^】]+)】([^\n]+)$", block)]
        cards.append({"ganzhi": hit.group(1), "status": hit.group(2), "rows": rows})
    return cards


def main() -> None:
    capture = json.loads((HERE / "month_year_2026_reference.json").read_text(encoding="utf-8"))
    reference = parse_year_cards(capture["year_text"])
    local = get_year_sha(2026, 1)["cards"]
    checks = []
    for index, (site, computed) in enumerate(zip(reference, local)):
        local_rows = [(row["name"], row["value"]) for row in computed["rows"]]
        checks.append({
            "year": computed["year"],
            "ganzhi_equal": site["ganzhi"] == computed["ganzhi"],
            "rows_equal": site["rows"] == local_rows,
            "site_status": site["status"],
            "predicted_status_from_sansha": "不利" if computed["san_sha_hits"] else "大利",
            "row_differences": [
                {"index": i, "site": site["rows"][i] if i < len(site["rows"]) else None,
                 "local": local_rows[i] if i < len(local_rows) else None}
                for i in range(max(len(site["rows"]), len(local_rows)))
                if (site["rows"][i] if i < len(site["rows"]) else None)
                != (local_rows[i] if i < len(local_rows) else None)
            ],
        })
    month = capture["month_text"].split("\n\n丙申月吉神表", 1)[0]
    month_rows = [tuple(match.groups()) for match in re.finditer(r"(?m)^【([^】]+)】([^\n]+)$", month)]
    result = {
        "source": "visible Edge site month/year panes, captured without a new search submission",
        "year_cards_site": len(reference),
        "year_cards_local": len(local),
        "year_checks": checks,
        "year_rows_all_equal": len(reference) == len(local) and all(x["rows_equal"] and x["ganzhi_equal"] for x in checks),
        "year_status_sansha_all_equal": all(x["site_status"] == x["predicted_status_from_sansha"] for x in checks),
        "bing_shen_month_title": month.splitlines()[0],
        "bing_shen_month_rows": month_rows,
        "bing_shen_month_row_count": len(month_rows),
    }
    (HERE / "panel_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("year_cards_site", "year_cards_local", "year_rows_all_equal", "year_status_sansha_all_equal", "bing_shen_month_row_count")}, ensure_ascii=False))
    for check in checks:
        if check["row_differences"]:
            print(json.dumps({"year": check["year"], "differences": check["row_differences"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
