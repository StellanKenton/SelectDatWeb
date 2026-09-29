"""Check mountain sha fields against saved original-site cards and UI filter behavior."""

import json
from datetime import date, datetime
from pathlib import Path
import re
import unittest

from core.mountain_rules import CLASH, controls_shan_yun, day_xiaomie, sansha_for_mountain, shan_yun_element
from core.shanjia import MOUNTAINS, MOUNTAIN_ID_BY_NAME, _flying_seat_stars, calculate_days


ROOT = Path(__file__).resolve().parents[1]
CAPTURES = (
    ("visual_reference_dingyou_2026.json", "壬"),
    ("visual_reference_jia_2026.json", "甲"),
    ("visual_reference_gen_2026.json", "艮"),
    ("visual_reference_geng_2026.json", "庚"),
)


class MountainRuleParityTest(unittest.TestCase):
    def test_xiaomie_visible_site_cases_and_filter(self):
        captured = json.loads((ROOT / "output" / "xiaomie_xun_2027_0726_evaluation.json").read_text(encoding="utf-8"))
        before = json.loads((ROOT / "output" / "xiaomie_xun_2027_0726_off_reference.json").read_text(encoding="utf-8"))
        after = json.loads((ROOT / "output" / "xiaomie_xun_2027_0726_on_reference.json").read_text(encoding="utf-8"))
        october = json.loads((ROOT / "output" / "xiaomie_xun_2027_1024_evaluation.json").read_text(encoding="utf-8"))
        xin = json.loads((ROOT / "output" / "xiaomie_xin_2027_0726_evaluation.json").read_text(encoding="utf-8"))
        kun = json.loads((ROOT / "output" / "xiaomie_kun_2031_0522_evaluation.json").read_text(encoding="utf-8"))
        preterm = json.loads((ROOT / "output" / "xiaomie_ren_2027_0621_evaluation.json").read_text(encoding="utf-8"))
        self.assertIn("日消灭煞", captured["center_text"])
        self.assertIn("日消灭煞", october["center_text"])
        self.assertIn("日消灭煞", xin["center_text"])
        self.assertNotIn("日消灭煞", preterm["center_text"])
        self.assertNotIn("日消灭煞", kun["center_text"])
        self.assertEqual((before["result_count"], after["result_count"]), (31, 30))
        self.assertTrue(before["target_date_present"])
        self.assertFalse(after["target_date_present"])
        self.assertFalse(day_xiaomie("辛未", datetime(2027, 6, 21, 0), "壬"))
        self.assertTrue(day_xiaomie("丙午", datetime(2027, 7, 26, 0), "巽"))
        self.assertTrue(day_xiaomie("丙子", datetime(2027, 10, 24, 0), "巽"))
        self.assertTrue(day_xiaomie("丙午", datetime(2027, 7, 26, 0), "辛"))
        self.assertFalse(day_xiaomie("壬戌", datetime(2031, 5, 22, 0), "坤"))

        payload = {"start_date": "2027-07-26", "end_date": "2027-07-26",
                   "calendar_mode": "公历", "calendar_year": 2027, "calendar_month": 7,
                   "calendar_day": 26, "use_type": "建造", "mountain_id": 11,
                   "level": "全部", "yiji_mode": "off", "hours": [0],
                   "sha_filters": [], "jian_filters": []}
        unfiltered = calculate_days(payload)
        filtered = calculate_days(payload | {"sha_filters": ["日消灭煞"]})
        self.assertEqual(unfiltered["count"], 1)
        self.assertTrue(unfiltered["results"][0]["day_xiaomie"])
        self.assertEqual(filtered["count"], 0)
        self.assertEqual(filtered["active_sha_filters"], ["日消灭煞"])
        evaluated = calculate_days(payload | {"sha_filters": ["日消灭煞"],
                                             "evaluation_mode": True})
        self.assertEqual(evaluated["count"], 1)
        self.assertTrue(evaluated["results"][0]["day_xiaomie"])

        month = payload | {"start_date": "2027-07-01", "end_date": "2027-07-31",
                           "calendar_day": 0}
        month_before = calculate_days(month)
        month_after = calculate_days(month | {"sha_filters": ["日消灭煞"]})
        self.assertEqual((month_before["count"], month_after["count"]), (31, 30))
        self.assertEqual({item["date"] for item in month_before["results"]} -
                         {item["date"] for item in month_after["results"]},
                         {"2027-07-26"})

    def test_visible_five_yellow_and_shan_yun_labels(self):
        checked = 0
        for filename, mountain in CAPTURES:
            capture = json.loads((ROOT / "output" / filename).read_text(encoding="utf-8"))
            cards = capture["center_text"].split("[打印] ")[1:]
            self.assertEqual(len(cards), 31)
            for card in cards:
                hit = re.search(r"公历:(\d+)月(\d+)日", card)
                day = date(2026, int(hit[1]), int(hit[2]))
                block = card.split("\n斗首择日\n", 1)[1].split("\n" + mountain + "山煞\n", 1)[0].splitlines()
                pillars = [block[8 + i] + block[12 + i] for i in range(4)]
                text = card.split("\n" + mountain + "山煞\n", 1)[1].split("\n杀师煞\n", 1)[0]
                labels = set(text.splitlines())
                stars = _flying_seat_stars(day, 0, MOUNTAINS[MOUNTAIN_ID_BY_NAME[mountain]])
                with self.subTest(mountain=mountain, day=day):
                    for label, index in (("月五黄煞", 1), ("日五黄煞", 2), ("时五黄煞", 3)):
                        self.assertEqual(label in labels, stars[index] == 5, label)
                    for label, index in (("月克山运", 1), ("日克山运", 2), ("时克山运", 3)):
                        self.assertEqual(label in labels,
                                         controls_shan_yun(pillars[index], pillars[0], mountain), label)
                    self.assertIn("山运" + shan_yun_element(pillars[0], mountain), labels)
                checked += 1
        self.assertEqual(checked, 124)

    def test_new_filters_change_only_matching_lessons(self):
        base = {"start_date": "2026-09-16", "end_date": "2026-09-16",
                "calendar_mode": "公历", "calendar_year": 2026, "calendar_month": 9,
                "calendar_day": 16, "use_type": "建造", "mountain_id": 1,
                "level": "全部", "yiji_mode": "off", "hours": [0],
                "sha_filters": [], "jian": "亥巳", "jian_filters": []}
        self.assertEqual(calculate_days(base)["count"], 1)
        self.assertEqual(calculate_days(base | {"jian_filters": ["日冲兼山"]})["count"], 0)
        self.assertEqual(calculate_days(base | {"jian_filters": ["兼山月三杀"]})["count"], 1)

    def test_visible_jian_clash_labels(self):
        # The selected 兼山 is inferred from the original card's month/day clash
        # labels.  艮山 also exposes eight independently checkable 日兼三杀 labels.
        chosen = {"壬": "亥", "甲": "卯", "艮": "丑", "庚": "酉"}
        checked = 0
        for filename, mountain in CAPTURES:
            capture = json.loads((ROOT / "output" / filename).read_text(encoding="utf-8"))
            jian = chosen[mountain]
            for card in capture["center_text"].split("[打印] ")[1:]:
                block = card.split("\n斗首择日\n", 1)[1].split("\n" + mountain + "山煞\n", 1)[0].splitlines()
                day_branch = block[14]
                labels = set(card.splitlines())
                with self.subTest(mountain=mountain, day=block[10] + day_branch):
                    self.assertEqual("月冲兼" in labels, CLASH["酉"] == jian)
                    self.assertEqual("日冲兼" in labels, CLASH[day_branch] == jian)
                    if mountain == "艮":
                        self.assertEqual("日兼三杀" in labels, sansha_for_mountain(day_branch, jian))
                checked += 1
        self.assertEqual(checked, 124)

    def test_month_star_switches_at_term_hour(self):
        mountain = MOUNTAINS[1]
        self.assertEqual(_flying_seat_stars(date(2026, 10, 8), 0, mountain)[1], 6)
        self.assertEqual(_flying_seat_stars(date(2026, 10, 8), 16, mountain)[1], 5)


if __name__ == "__main__":
    unittest.main()
