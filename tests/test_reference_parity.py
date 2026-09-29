"""Regression checks against saved UI results; these tests never contact the site."""

from __future__ import annotations

import json
import re
import unittest
from datetime import date
from pathlib import Path

from core.shanjia import (
    MOUNTAINS,
    _flying_seat_day_hour_stars,
    _flying_seat_stars,
    _hits_bang_yinfu,
    _hour_rows,
    calculate_days,
    get_month_sha,
    get_year_sha,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"


def capture(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def site_dates(text: str, year: int = 2026) -> list[str]:
    return [f"{year}-{int(month):02d}-{int(day):02d}" for month, day in
            re.findall(r"公历:(\d+)月(\d+)日", text)]


def site_year_cards(text: str) -> list[dict]:
    headings = list(re.finditer(r"(?m)^([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])年凶煞【点击选择】(大利|不利)$", text))
    cards = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.end():end].split("【点击展开凶煞】", 1)[0]
        rows = [tuple(hit.groups()) for hit in re.finditer(r"(?m)^【([^】]+)】([^\n]+)$", body)]
        cards.append({"ganzhi": heading.group(1), "status": heading.group(2), "rows": rows})
    return cards


class ReferenceParityTest(unittest.TestCase):
    def test_bing_shen_month_table_full_visible_text(self):
        source = capture("month_year_2026_reference.json")["month_text"]
        prefix = source.split("\n\n【泄】 庚寅月【点击添加】", 1)[0]
        local = get_month_sha(2026, "丙申")
        self.assertTrue(local["reference_verified"])
        self.assertEqual(local["visible_text"], prefix)
        self.assertEqual((len(local["bad"]), len(local["good"])), (29, 29))
        self.assertFalse(get_month_sha(2027, "丙申")["reference_verified"])

    def test_saved_ding_you_month_table_and_page_sample(self):
        month = get_month_sha(2026, "丁酉")
        self.assertTrue(month["reference_verified"])
        self.assertEqual((len(month["bad"]), len(month["good"])), (29, 29))
        self.assertEqual(month["visible_text"], capture("month_dingyou_2026_selected_reference.json")["visible_text"])
        self.assertIn("【五黄煞】离宫", month["visible_text"])
        site = capture("visual_reference_dingyou_2026.json")
        self.assertEqual(len(site_dates(site["center_text"])), 31)
        local = calculate_days({"start_date": "2026-01-15", "end_date": "2027-02-15",
                                "ganzhi_year": "丙午", "ganzhi_month": "丁酉",
                                "use_type": "建造", "mountain_id": 1,
                                "evaluation_mode": True, "hours": [0]})
        self.assertEqual([row["date"] for row in local["results"]], site_dates(site["center_text"]))
        first = local["results"][0]
        self.assertEqual(first["flying_stars"], {"facing": "5544", "center": "1199", "seat": "6655"})
        self.assertEqual(first["ji_shen"][:3], ["月德合", "月财", "神在"])
        self.assertEqual(first["men_guang"], "损畜")
        self.assertEqual(first["hour_signs"], ["时吉", "罗纹", "司命", "阴贵"])
        self.assertEqual(first["jieqi_times"][0], {"name": "白露", "time": "2026-09-07 22:40:59"})

    def test_calendar_modes_keep_selected_date_scope(self):
        base = {"start_date": "2026-09-01", "end_date": "2026-09-30",
                "use_type": "建造", "mountain_id": 1,
                "evaluation_mode": True, "hours": [0]}
        all_september = calculate_days({**base, "calendar_mode": "公历",
                                        "calendar_year": 2026, "calendar_month": 9})
        self.assertEqual(all_september["count"], 30)
        one_day = calculate_days({**base, "calendar_mode": "公历",
                                  "calendar_year": 2026, "calendar_month": 9, "calendar_day": 8})
        self.assertEqual([row["date"] for row in one_day["results"]], ["2026-09-08"])
        lunar = calculate_days({**base, "calendar_mode": "农历",
                                "calendar_year": 2026, "calendar_month": 7})
        self.assertTrue(lunar["results"])
        self.assertTrue(all(row["date"] < "2026-09-11" for row in lunar["results"]))

    def test_two_mountains_ten_year_cards_each(self):
        for mountain_id, source_name in (
            (1, "month_year_2026_reference.json"),
            (13, "year_bing_mountain_2026_reference.json"),
        ):
            with self.subTest(mountain_id=mountain_id):
                site = site_year_cards(capture(source_name)["year_text"])
                local = get_year_sha(2026, mountain_id)["cards"]
                self.assertEqual(len(site), len(local), 10)
                for expected, actual in zip(site, local):
                    self.assertEqual(actual["ganzhi"], expected["ganzhi"])
                    self.assertEqual(actual["status"], expected["status"])
                    self.assertEqual([(r["name"], r["value"]) for r in actual["rows"]], expected["rows"])

    def test_year_expansions_match_visible_site_cards(self):
        checked = set()
        for filename in ("year_expanded_reference_2026_2035.json",
                         "year_expanded_reference_2031_2040.json"):
            for expected in capture(filename):
                year = expected["year"]
                actual = get_year_sha(year, 17)["cards"][0]
                self.assertEqual(actual["ganzhi"], expected["ganzhi"])
                self.assertTrue(actual["reference_expanded_verified"])
                self.assertEqual([(row["name"], row["value"]) for row in actual["extra_sha"]],
                                 [(row["name"], row["value"]) for row in expected["sha"]])
                self.assertEqual([(row["name"], row["value"]) for row in actual["good_rows"]],
                                 [(row["name"], row["value"]) for row in expected["good"]])
                checked.add(year)
        self.assertEqual(checked, set(range(2026, 2041)))
        self.assertEqual(len(get_year_sha(2031, 17)["cards"][0]["extra_sha"]), 43)
        self.assertEqual(len(get_year_sha(2031, 17)["cards"][0]["good_rows"]), 25)

        later = capture("year_sha_visible_2031_2040.json")["cards"]
        for expected in later:
            actual = get_year_sha(expected["year"], 17)["cards"][0]
            self.assertEqual([(row["name"], row["value"]) for row in actual["rows"]],
                             [tuple(row) for row in expected["rows"]])

    def test_2026_september_flying_day_hour_stars(self):
        text = capture("B02_reference.json")["center_text"]
        cards = text.split("[打印] ")[1:]
        self.assertEqual(len(cards), 30)
        for card in cards:
            day = int(re.search(r"公历:9月(\d+)日", card).group(1))
            seat = re.search(r"(?m)^([1-9]{4})坐$", card).group(1)
            stars = _flying_seat_day_hour_stars(date(2026, 9, day), 0, MOUNTAINS[1])
            self.assertEqual(stars, (int(seat[2]), int(seat[3])), day)
            self.assertEqual("五黄重叠" in card, stars == (5, 5), day)
            self.assertEqual("二五交加" in card, set(stars) == {2, 5}, day)

    def test_60_saved_cards_time_bang_yinfu(self):
        for year, filename in ((2011, "B01_reference.json"), (2026, "B02_reference.json")):
            cards = capture(filename)["center_text"].split("[打印] ")[1:]
            self.assertEqual(len(cards), 30)
            for card in cards:
                month, day = (int(x) for x in re.search(r"公历:(\d+)月(\d+)日", card).groups())
                hour_gz = _hour_rows(date(year, month, day), [0], MOUNTAINS[1])[0]["ganzhi"]
                self.assertEqual(_hits_bang_yinfu(hour_gz, MOUNTAINS[1]),
                                 "时傍阴府" in card, (year, month, day))

    def test_60_saved_calendar_rows_reach_calculation_api(self):
        calendar = json.loads((ROOT / "core" / "almanac_reference.json").read_text(encoding="utf-8"))
        for year in (2011, 2026):
            local = calculate_days({"start_date": f"{year}-09-01", "end_date": f"{year}-09-30",
                                    "use_type": "建造", "mountain_id": 1, "level": "全部",
                                    "edition": "不显示", "hours": [0], "sha_filters": []})
            self.assertEqual(local["count"], 30)
            for lesson in local["results"]:
                source = calendar[lesson["date"]]
                self.assertEqual(lesson["yi"], source["yi"], lesson["date"])
                self.assertEqual(lesson["ji"], source["ji"], lesson["date"])
                self.assertEqual(lesson["reference_grade_label"], source["ren_hour0_grade"], lesson["date"])

    def test_60_site_cards_four_star_overlap_labels(self):
        for filename in ("B01_reference.json", "B02_reference.json"):
            cards = capture(filename)["center_text"].split("[打印] ")[1:]
            self.assertEqual(len(cards), 30)
            for card in cards:
                seat = re.search(r"(?m)^([1-9]{4})坐$", card).group(1)
                self.assertEqual("五黄重叠" in card, seat.count("5") >= 2, filename)
                self.assertEqual("二五交加" in card, "2" in seat and "5" in seat, filename)
        # In 2026 丁酉月, year and month both place 五黄 in 丙山's 离宫.
        self.assertEqual(_flying_seat_stars(date(2026, 9, 8), 0, MOUNTAINS[13])[:2], (5, 5))

    def test_six_right_search_date_sets(self):
        samples = (
            ("B02_right_reference.json", 1, "大吉", "协纪版", None),
            ("B15_right_all_reference.json", 1, "全部", "协纪版", None),
            ("B15_right_yiji_off_reference.json", 1, "全部", "不显示", None),
            ("B07_bing_mountain_reference.json", 13, "全部", "不显示", None),
            ("B07_no_month_sansha_reference.json", 13, "全部", "不显示", "capture"),
            ("B07_no_month_time_sansha_reference.json", 13, "全部", "不显示", "capture"),
        )
        for filename, mountain_id, level, edition, filter_mode in samples:
            with self.subTest(filename=filename):
                source = capture(filename)
                filters = None
                if filter_mode == "capture":
                    filters = [x["value"] for x in source["active_filters"] if x["name"] == "Arry_xiongsha[]"]
                payload = {"start_date": "2026-09-01", "end_date": "2026-09-30",
                           "use_type": "建造", "mountain_id": mountain_id, "level": level,
                           "edition": edition, "hours": [0]}
                if filters is not None:
                    payload["sha_filters"] = filters
                local = calculate_days(payload)
                self.assertEqual([x["date"] for x in local["results"]], site_dates(source["center_text"]))
                self.assertEqual(local["count"], source["result_count"])

if __name__ == "__main__":
    unittest.main()
