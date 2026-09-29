"""Extract visible 宜/忌 rows from saved monthly evaluation cards.

This reads local gold captures only and never contacts the reference site.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ((2011, "B01_reference.json"), (2026, "B02_reference.json"),
           (2026, "visual_reference_dingyou_2026.json"))


def main() -> None:
    rows = {}
    for year, filename in SOURCES:
        capture = json.loads((ROOT / "output" / filename).read_text(encoding="utf-8"))
        for card in capture["center_text"].split("[打印] ")[1:]:
            date_hit = re.search(r"公历:(\d+)月(\d+)日", card)
            yi_hit = re.search(r"(?m)^宜事: ([^\n]*)$", card)
            ji_hit = re.search(r"(?m)^忌事: ([^\n]*)$", card)
            grade_hit = re.search(r"壬山属水\s*\.?\s*([^\n]+)", card)
            good_hit = re.search(r"(?m)^吉神: ([^\n]*)$", card)
            bad_hit = re.search(r"(?m)^凶煞: ([^\n]*)$", card)
            if not all((date_hit, yi_hit, ji_hit, grade_hit, good_hit, bad_hit)):
                raise ValueError(f"Incomplete calendar card in {filename}")
            month, day = (int(part) for part in date_hit.groups())
            key = f"{year:04d}-{month:02d}-{day:02d}"
            good_text, _, compass = good_hit.group(1).partition(" 福神:")
            star_hits = dict((direction, stars) for stars, direction in
                             re.findall(r"(?m)^([1-9]{4})(向|中|坐)$", card))
            term_block = card.split("节气时间\n", 1)[-1]
            terms = [{"name": name, "time": time} for name, time in
                     re.findall(r"(?m)^([^\n:]+):(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$", term_block)]
            tai = re.search(r"胎神占\n([^\n]+)\n\.\n([^\n]+)", card)
            shan = re.search(r"壬山煞\n(.*?)\n飞星\n", card, re.DOTALL)
            men_block = card.split("门光星\n", 1)[-1].split("\n周堂", 1)[0]
            men_values = [line.strip() for line in men_block.splitlines() if line.strip() not in {"", "."}]
            hour_block = re.search(r"(?m)^\d+点\n(.*?)\n壬山属水\n", card, re.DOTALL)
            rows[key] = {
                "yi": [part for part in yi_hit.group(1).split(".") if part],
                "ji": [part for part in ji_hit.group(1).split(".") if part],
                "ji_shen": [part for part in good_text.split(".") if part],
                "xiong_sha": [part for part in bad_hit.group(1).split(".") if part],
                "compass_gods_text": "福神:" + compass if compass else "",
                "day_position_tai": " ".join(tai.groups()) if tai else "",
                "men_guang": men_values[-1] if men_values else "",
                "jieqi_times": terms,
                "ren_hour0_flying_stars": {"facing": star_hits.get("向", ""),
                                                  "center": star_hits.get("中", ""),
                                                  "seat": star_hits.get("坐", "")},
                "ren_hour0_shan_sha": shan.group(1).splitlines() if shan else [],
                "ren_hour0_hour_signs": hour_block.group(1).splitlines() if hour_block else [],
                "ren_hour0_grade": grade_hit.group(1).strip(),
                "source": filename,
            }
    if len(rows) != 68:
        raise ValueError(f"Expected 68 distinct saved daily cards, found {len(rows)}")
    target = ROOT / "core" / "almanac_reference.json"
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} reference calendar rows to {target}")


if __name__ == "__main__":
    main()
