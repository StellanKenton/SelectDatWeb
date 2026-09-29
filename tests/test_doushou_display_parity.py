"""Compare rendered lesson data with saved visible original-site cards."""

import json
import re
from pathlib import Path
import unittest

from core.shanjia import calculate_days, get_options


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "visual_reference_dingyou_2026.json",
    "visual_reference_jia_2026.json",
    "visual_reference_gen_2026.json",
    "visual_reference_geng_2026.json",
    "visual_reference_kun_2026_uia.json",
    "visual_reference_ren_2031_uia.json",
    "xiaomie_xun_2027_0726_off_reference.json",
)
MOUNTAIN_IDS = {item["name"]: item["id"] for item in get_options()["mountains"]}
SOURCE_JIAN = {
    "visual_reference_dingyou_2026.json": "亥巳",
    "visual_reference_jia_2026.json": "卯酉",
    "visual_reference_gen_2026.json": "丑未",
    "visual_reference_geng_2026.json": "酉卯",
    "xiaomie_xun_2027_0726_off_reference.json": "辰戌",
}


def visible_cards(source):
    text = source.get("center_text") or source.get("visible_text", "")
    mountain = source["mountain"]
    for raw in re.split(r"\[打印\]\s*", text)[1:]:
        lines = raw.splitlines()
        match = re.search(r"农历:(\d{4}).*?公历:(\d{1,2})月(\d{1,2})日", lines[0])
        if not match:
            continue
        year, month, day = map(int, match.groups())
        date = f"{year:04d}-{month:02d}-{day:02d}"
        grade = next(i + 1 for i, line in enumerate(lines)
                     if line.startswith(mountain + "山属"))
        hour = lines.index("0点")
        men = next(i for i, line in enumerate(lines) if line.startswith("门光星"))
        men_value = next(line for line in lines[men + 1:men + 4]
                         if line.strip() and line.strip() != "\ufffc")
        tai, zhou = lines.index("胎神占"), lines.index("周堂")
        shan = lines.index(mountain + "山煞")
        fly, master, jieqi = (lines.index("飞星", shan), lines.index("杀师煞", shan),
                              lines.index("节气时间", shan))
        stars = {}
        for line in lines[fly + 1:master]:
            hit = re.fullmatch(r"([1-9]{4})([向中坐])", line)
            if hit:
                stars[{"向": "facing", "中": "center", "坐": "seat"}[hit[2]]] = hit[1]
        terms = [line for line in lines[jieqi + 1:]
                 if re.fullmatch(r"[^:\n]+:\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", line)]
        ds = lines.index("斗首择日")
        header = lines[0]
        yield date, {
            "grade": lines[grade].removeprefix("."),
            "top_relations": lines[grade + 1:grade + 5],
            "bottom_relations": lines[grade + 13:grade + 17],
            "nayin": lines[grade + 18:grade + 22],
            "hour_signs": lines[hour + 1:grade - 1],
            "men_guang": men_value,
            "tai": lines[tai + 1] + " " + lines[tai + 3],
            "zhoutang": lines[zhou + 1] + " · " + lines[zhou + 3],
            "zhi_xing": re.search(r"十二建星:([^ ]+)", header)[1],
            "xiu": re.search(r"二十八宿:([^ ]+)", header)[1],
            "shan_sha": [line for line in lines[shan + 1:fly]
                         if line.strip() and line.strip() != "\ufffc"],
            "flying_stars": stars,
            "master_sha": lines[master + 1:jieqi],
            "jieqi_times": terms,
            "doushou": lines[ds + 1:ds + 33],
        }


class DoushouDisplayParityTest(unittest.TestCase):
    def test_saved_visible_cards_match_local_fields(self):
        total = 0
        for filename in SOURCES:
            source = json.loads((ROOT / "output" / filename).read_text(encoding="utf-8"))
            originals = list(visible_cards(source))
            mountain = source["mountain"]
            data = calculate_days({
                "start_date": originals[0][0], "end_date": originals[-1][0],
                "evaluation_mode": True, "mountain_id": MOUNTAIN_IDS[mountain],
                "jian": (re.search(r"【([^】]+)】", source["jian"]).group(1)
                         if source.get("jian") else SOURCE_JIAN.get(filename, "")),
                "hours": [0],
            })
            local = {card["date"]: card for card in data["results"]}
            self.assertEqual(list(local), [date for date, _ in originals], filename)
            for date, expected in originals:
                with self.subTest(source=filename, date=date):
                    card = local[date]
                    self.assertEqual(card["reference_grade_label"] or card["level_name"],
                                     expected["grade"])
                    self.assertEqual(card["pillar_top_relations"], expected["top_relations"])
                    self.assertEqual(card["pillar_bottom_relations"], expected["bottom_relations"])
                    self.assertEqual(card["pillar_nayin_elements"], expected["nayin"])
                    self.assertEqual(card["hour_signs"], expected["hour_signs"])
                    self.assertEqual(card["men_guang"], expected["men_guang"])
                    self.assertEqual(card["day_position_tai"], expected["tai"])
                    self.assertEqual(card["zhoutang"], expected["zhoutang"])
                    self.assertEqual(card["zhi_xing"] + "日", expected["zhi_xing"])
                    self.assertEqual(card["xiu"] + "宿" + card["xiu_luck"], expected["xiu"])
                    self.assertEqual(card["shan_sha_labels"], expected["shan_sha"])
                    self.assertEqual(card["flying_stars"], expected["flying_stars"])
                    self.assertEqual(card["master_sha_labels"], expected["master_sha"])
                    self.assertEqual([f"{term['name']}:{term['time']}"
                                      for term in card["jieqi_times"]], expected["jieqi_times"])
                    rows = card["doushou"]["pillars"]
                    observed_ds = [value for field in (
                        "upper_star", "upper_element", "ganzhi", "upper_stage",
                        "lower_star", "lower_element", "lower_stage")
                        for value in ([row[field] for row in rows] if field != "ganzhi" else
                                      [row["ganzhi"][0] for row in rows] +
                                      [row["ganzhi"][1] for row in rows])]
                    self.assertEqual(observed_ds, expected["doushou"])
                    total += 1
        self.assertEqual(total, 216)


if __name__ == "__main__":
    unittest.main()
