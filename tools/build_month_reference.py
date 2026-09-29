"""Extract the twelve 2026 month tables from one saved visible pane."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        hit = re.fullmatch(r"【([^】]+)】\s*(.*)", line)
        if hit:
            rows.append([hit.group(1), hit.group(2)])
    return rows


def main() -> None:
    capture = json.loads((ROOT / "output" / "month_year_2026_reference.json").read_text(encoding="utf-8"))
    text = capture["month_text"]
    list_heading = re.compile(r"(?m)^【([旺生耗泄克])】 ([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])月【点击添加】$")
    good_heading = re.compile(r"(?m)^([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])月吉神表$")
    listed = list(list_heading.finditer(text))
    goods = list(good_heading.finditer(text))
    if len(listed) != 12 or len(goods) != 13:
        raise ValueError(f"Expected 12 monthly lists plus selected good table, got {len(listed)} and {len(goods)}")
    if not text.startswith("丙申月凶煞表\n") or goods[0].group(1) != "丙申":
        raise ValueError("Unexpected selected month")
    selected_bad = text[:goods[0].start()].strip()
    selected_good = text[goods[0].start():listed[0].start()].strip()
    ding_you = json.loads((ROOT / "output" / "month_dingyou_2026_selected_reference.json").read_text(encoding="utf-8"))["visible_text"]
    ding_bad, ding_good = ding_you.split("\n\n丁酉月吉神表\n", 1)
    ding_good = "丁酉月吉神表\n" + ding_good
    data = {}
    for index, heading in enumerate(listed):
        month = heading.group(2)
        end = listed[index + 1].start() if index + 1 < len(listed) else goods[1].start()
        bad_body = text[heading.end():end].strip()
        good_match = next((match for match in goods[1:] if match.group(1) == month), None)
        if good_match is None:
            raise ValueError(f"Missing good table for {month}")
        good_index = goods.index(good_match)
        good_end = goods[good_index + 1].start() if good_index + 1 < len(goods) else len(text)
        good_body = text[good_match.end():good_end].strip()
        bad_text = f"{month}月凶煞表\n{bad_body}"
        good_text = f"{month}月吉神表\n{good_body}"
        if month == "丙申":
            bad_text, good_text = selected_bad, selected_good
        elif month == "丁酉":
            bad_text, good_text = ding_bad, ding_good
        data[f"2026-{month}"] = {
            "year": 2026,
            "ganzhi_month": month,
            "relation_to_saved_mountain": heading.group(1),
            "bad": parse_rows(bad_text),
            "good": parse_rows(good_text),
            "visible_text": bad_text + "\n\n" + good_text,
            "source": "output/month_year_2026_reference.json",
        }
    if len(data["2026-丙申"]["bad"]) != 29 or len(data["2026-丙申"]["good"]) != 29:
        raise ValueError("The selected 丙申 table changed unexpectedly")
    target = ROOT / "core" / "month_sha_reference.json"
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(data)} monthly tables for 2026")


if __name__ == "__main__":
    main()
