"""Use saved monthly cards to audit selected sha filters, without site requests."""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def cards(text: str) -> list[str]:
    return ["[打印] " + chunk for chunk in text.split("[打印] ")[1:]]


def card_rows(text: str) -> list[dict]:
    result = []
    for card in cards(text):
        match = re.search(r"公历:(\d+)月(\d+)日", card)
        if not match:
            continue
        sep = card.split("\n壬山煞\n", 1)
        sha = sep[1].split("\n飞星\n", 1)[0].splitlines() if len(sep) == 2 else []
        result.append({"date": f"2026-{int(match.group(1)):02d}-{int(match.group(2)):02d}", "sha": sha, "card": card})
    return result


def main() -> None:
    top = card_rows(read("B02_reference.json")["center_text"])
    right = read("B15_right_all_reference.json")
    included = {row["date"] for row in card_rows(right["center_text"])}
    filters = {item["value"] for item in right["active_filters"] if item["name"] == "Arry_xiongsha[]"}
    rows = []
    for row in top:
        sha = [item for item in row["sha"] if item and not item.startswith("山运")]
        hits = [item for item in sha if item in filters]
        ji_match = re.search(r"(?m)^忌事: ([^\n]*)", row["card"])
        ji = ji_match.group(1) if ji_match else ""
        rows.append({"date": row["date"], "included_by_right_search": row["date"] in included,
                     "visible_sha": sha, "selected_filter_name_hits": hits,
                     "site_ji_contains_竖造": "竖造" in ji, "site_ji_line": ji})
    output = {
        "source": "B02 top evaluation cards and B15 right filtered cards",
        "selected_sha_filters": sorted(filters),
        "top_dates": len(top),
        "right_dates": len(included),
        "rows": rows,
        "false_negative_candidates": [r["date"] for r in rows if not r["included_by_right_search"] and not r["selected_filter_name_hits"]],
        "included_with_named_hit": [r["date"] for r in rows if r["included_by_right_search"] and r["selected_filter_name_hits"]],
    }
    (HERE / "day_filter_analysis.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"top_dates": len(top), "right_dates": len(included),
                      "excluded_without_visible_named_hit": output["false_negative_candidates"],
                      "included_with_visible_named_hit": output["included_with_named_hit"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
