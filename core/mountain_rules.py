"""Mountain sha rules transcribed from the user's 二十四山 Word table."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import json
from pathlib import Path

from lunar_python import Solar


REFERENCE = json.loads(Path(__file__).with_name("mountain_rule_reference.json").read_text(encoding="utf-8"))
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
GAN_PAIRS = ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")
CLASH = {"子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌", "巳": "亥",
         "午": "子", "未": "丑", "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳"}

# OCR prose is checked against the visible Word table.  The 坤 row wrongly says
# "坐丁山", so it is intentionally absent until separately confirmed.
DAY_XIAOMIE = {
    "壬": (("夏至", "辛未"),),
    "癸": (("冬至", "庚午"),),
    "艮": (("处暑", "乙卯"), ("小雪", "癸酉")),
    "甲": (("夏至", "辛丑"), ("秋分", "辛未")),
    "乙": (("冬至", "庚子"), ("春分", "庚午")),
    "巽": (("霜降", "丙子"), ("大暑", "丙午")),
    "丙": (("处暑", "乙卯"), ("小雪", "癸酉")),
    "丁": (("雨水", "甲辰"), ("小满", "壬戌")),
    "庚": (("大寒", "丁卯"), ("谷雨", "丁酉")),
    "辛": (("霜降", "丙子"), ("大暑", "丙午")),
    "乾": (("夏至", "辛丑"), ("秋分", "辛未")),
}


def shan_yun_element(year_ganzhi: str, mountain: str) -> str:
    gan = year_ganzhi[0]
    pair = next(pair for pair in GAN_PAIRS if gan in pair)
    return REFERENCE["shan_yun_by_year_gan_pair"][mountain][pair]


def nayin_element(ganzhi: str) -> str:
    return REFERENCE["nayin_by_ganzhi"][ganzhi]


def controls_shan_yun(ganzhi: str, year_ganzhi: str, mountain: str) -> bool:
    return CONTROLS[nayin_element(ganzhi)] == shan_yun_element(year_ganzhi, mountain)


def day_flow_taisui(ganzhi: str, mountain: str) -> bool:
    return ganzhi in REFERENCE["mountains"][mountain]["day_flow_taisui"]


def sansha_for_mountain(branch: str, mountain: str) -> bool:
    return branch in REFERENCE["mountains"][mountain]["sansha_branches"]


def jian_mountain(jian: str) -> str | None:
    return jian[0] if len(jian) == 2 and jian[0] in REFERENCE["mountains"] else None


def day_xiaomie(ganzhi: str, when: date | datetime, mountain: str) -> bool:
    rules = DAY_XIAOMIE.get(mountain, ())
    if not rules:
        return False
    # The original site starts the window at the actual solar-term time.
    # A date-only comparison incorrectly marks 壬山 2027-06-21 子时,
    # before 夏至 at 22:10, as 日消灭煞.
    at = when if isinstance(when, datetime) else datetime(when.year, when.month, when.day)
    matching = [(term, forbidden) for term, forbidden in rules if ganzhi == forbidden]
    if not matching:
        return False
    jieqi = Solar.fromYmd(at.year, at.month, at.day).getLunar().getJieQiTable()
    for term, _ in matching:
        solar = jieqi.get(term)
        if solar is None:
            continue
        term_time = datetime(solar.getYear(), solar.getMonth(), solar.getDay(),
                             solar.getHour(), solar.getMinute(), solar.getSecond())
        if term_time <= at < term_time + timedelta(days=5):
            return True
    return False
