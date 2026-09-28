from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re
from typing import Iterable

from lunar_python import Solar


GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

GAN_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
ZHI_ELEMENT = {
    "寅": "木", "卯": "木", "巳": "火", "午": "火",
    "申": "金", "酉": "金", "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

CLASH = {
    "子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}
LIU_HE = {
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午",
}
SAN_HE = (
    frozenset(("申", "子", "辰")),
    frozenset(("寅", "午", "戌")),
    frozenset(("亥", "卯", "未")),
    frozenset(("巳", "酉", "丑")),
)

# 网站 topzeri_info.php 的“手动添加利月”说明，用于下拉提示。
MONTH_ELEMENT_FAVORABLE = {
    "寅": {"木", "火"},
    "卯": {"木", "火"},
    "辰": {"土", "金"},
    "巳": {"火", "土"},
    "午": {"火", "土"},
    "未": {"土"},
    "申": {"金", "水"},
    "酉": {"金", "水"},
    "戌": {"土", "金"},
    "亥": {"水", "木"},
    "子": {"水", "木"},
    "丑": {"土", "金"},
}

# 网站 topzeri.js 的 arryueli0：点击“自动添加利月”时按二十四山直接取值。
# 这不是简单的“按五行反推月份”，个别山（丑、艮、辰、未、坤、戌等）有专门表。
MOUNTAIN_FAVORABLE_MONTHS = {
    1: ("申", "酉", "亥", "子"),
    2: ("申", "酉", "亥", "子"),
    3: ("申", "酉", "亥", "子"),
    4: ("巳", "辰", "丑"),
    5: ("巳", "午", "辰", "未", "戌", "丑"),
    6: ("寅", "卯", "亥", "子"),
    7: ("寅", "卯", "亥", "子"),
    8: ("寅", "卯", "亥", "子"),
    9: ("寅", "卯", "亥", "子"),
    10: ("巳", "午", "辰", "未"),
    11: ("寅", "卯", "亥", "子"),
    12: ("寅", "卯", "巳", "午"),
    13: ("寅", "卯", "巳", "午"),
    14: ("寅", "卯", "巳", "午"),
    15: ("寅", "卯", "巳", "午"),
    16: ("巳", "午", "未", "戌"),
    17: ("巳", "午", "辰", "未", "戌", "丑"),
    18: ("申", "酉", "辰", "戌", "丑"),
    19: ("申", "酉", "辰", "戌", "丑"),
    20: ("申", "酉", "辰", "戌", "丑"),
    21: ("申", "酉", "辰", "戌", "丑"),
    22: ("巳", "午", "戌"),
    23: ("申", "酉", "辰", "戌", "丑"),
    24: ("申", "酉", "亥", "子"),
}

# 三煞方：申子辰年煞南、寅午戌年煞北、亥卯未年煞西、巳酉丑年煞东。
SAN_SHA_DIRECTION = {
    "申": "南", "子": "南", "辰": "南",
    "寅": "北", "午": "北", "戌": "北",
    "亥": "西", "卯": "西", "未": "西",
    "巳": "东", "酉": "东", "丑": "东",
}

USE_TYPE_OPTIONS = [
    (0, "建造"), (1, "进神"), (2, "安门"), (3, "修方兼竖造"), (4, "修方"),
    (5, "装修"), (6, "入宅"), (7, "造门楼"), (8, "竖造动土"), (9, "修方动土"),
    (10, "开业"), (11, "作灶"), (12, "封顶上樑"), (13, "升层"), (14, "安葬"),
    (15, "附葬"), (16, "修坟"), (17, "旧坟立碑"), (18, "安葬破土"),
    (19, "附葬破土"), (20, "造坟"), (21, "启攒"), (30, "移香出火"),
    (31, "入宅归火"), (32, "拆卸"), (33, "避宅修方"), (34, "避宅装修"),
    (35, "空方动土"), (50, "其它"), (51, "交易"),
]
USE_TYPES = [label for _, label in USE_TYPE_OPTIONS]
USE_TYPE_CODE = {label: code for code, label in USE_TYPE_OPTIONS}


TRIGRAM_OPTIONS = [
    {"value": 1, "label": "【北方】坎卦", "name": "坎", "palace": "坎宫", "positions": ["壬", "子", "癸"]},
    {"value": 2, "label": "【西南】坤卦", "name": "坤", "palace": "坤宫", "positions": ["未", "坤", "申"]},
    {"value": 3, "label": "【东方】震卦", "name": "震", "palace": "震宫", "positions": ["甲", "卯", "乙"]},
    {"value": 4, "label": "【东南】巽卦", "name": "巽", "palace": "巽宫", "positions": ["辰", "巽", "巳"]},
    {"value": 5, "label": "【中央】中宫", "name": "中", "palace": "中宫", "positions": []},
    {"value": 6, "label": "【西北】乾卦", "name": "乾", "palace": "乾宫", "positions": ["戌", "乾", "亥"]},
    {"value": 7, "label": "【西方】兑卦", "name": "兑", "palace": "兑宫", "positions": ["庚", "酉", "辛"]},
    {"value": 8, "label": "【东北】艮卦", "name": "艮", "palace": "艮宫", "positions": ["丑", "艮", "寅"]},
    {"value": 9, "label": "【南方】离卦", "name": "离", "palace": "离宫", "positions": ["丙", "午", "丁"]},
]

REPAIR_DIRECTION_BUTTONS = [
    ("东南巽", "巽宫"), ("正南离", "离宫"), ("西南坤", "坤宫"),
    ("正东震", "震宫"), ("中", "中宫"), ("正西兑", "兑宫"),
    ("东北艮", "艮宫"), ("正北坎", "坎宫"), ("西北乾", "乾宫"),
]
REPAIR_POSITIONS = {item["palace"]: item["positions"] for item in TRIGRAM_OPTIONS}

BURIAL_USE_TYPES = {
    "安葬破土", "启攒", "造坟", "安葬", "修坟", "附葬破土", "附葬", "旧坟立碑"
}
REPAIR_USE_TYPES = {
    "修坟", "附葬破土", "附葬", "旧坟立碑", "修方动土",
    "修方", "升层", "装修", "修方兼竖造", "造门楼", "作灶"
}
NO_MOUNTAIN_USE_TYPES = {"其它", "交易", "空方动土"}
FACING_USE_TYPES = {"安门", "造门楼", "旧坟立碑"}
AUTO_SEAT_REPAIR_USE_TYPES = {"装修", "作灶", "升层", "修坟"}

WANGSHENG_MONTH_USE_TYPES = {
    "造门楼", "修方", "修方动土", "作灶", "装修", "升层", "进神",
    "入宅归火", "移香出火", "修方兼竖造", "修坟", "旧坟立碑", "附葬",
}

# 原站 topzeri_info.html 的 arryyongshiwangsheng 原值。
REFERENCE_MONTH_RELATIONS = {
    "建造": (),
    "进神": ("旺", "生", "耗"),
    "安门": (),
    "修方兼竖造": ("旺", "生"),
    "修方": ("旺", "生", "耗", "泄", "克"),
    "装修": ("旺", "生", "耗"),
    "入宅": (),
    "造门楼": ("旺", "生", "耗"),
    "竖造动土": (),
    "修方动土": ("旺", "生", "耗", "泄", "克"),
    "开业": (),
    "作灶": ("旺", "生", "耗", "泄", "克"),
    "封顶上樑": (),
    "升层": ("旺", "生", "耗"),
    "安葬": (),
    "附葬": ("旺", "生"),
    "修坟": ("旺", "生", "耗"),
    "旧坟立碑": ("旺", "生", "耗"),
    "安葬破土": (),
    "附葬破土": ("旺", "生", "耗", "泄", "克"),
    "造坟": (),
    "启攒": (),
    "移香出火": ("旺", "生", "耗"),
    "入宅归火": ("旺", "生", "耗"),
    "拆卸": (),
    "避宅修方": ("旺", "生", "耗", "泄"),
    "避宅装修": ("旺", "生", "耗", "泄"),
    "空方动土": (),
    "其它": (),
    "交易": (),
}


# 原站 topzeri_info.html 的 arr_shenshaguolv 原值。
REFERENCE_SHA_FILTERS = {
    "建造": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "月正阴府", "日正阴府", "时正阴府", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁", "日消灭煞", "日山方煞"),
    "进神": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁"),
    "安门": ("日冲山", "时冲山", "日三杀", "时三杀"),
    "修方兼竖造": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "月正阴府", "日正阴府", "时正阴府", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁", "日消灭煞", "日山方煞"),
    "修方": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日星曜煞", "时星曜煞", "天星煞", "地曜煞"),
    "装修": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁", "日消灭煞"),
    "入宅": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁"),
    "造门楼": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日星曜煞", "时星曜煞", "天星煞", "地曜煞"),
    "竖造动土": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日星曜煞", "时星曜煞", "天星煞", "地曜煞"),
    "修方动土": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日星曜煞", "时星曜煞", "天星煞", "地曜煞"),
    "开业": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞"),
    "作灶": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日星曜煞", "时星曜煞", "天星煞", "地曜煞"),
    "封顶上樑": ("日冲山", "时冲山", "日三杀", "时三杀"),
    "升层": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁", "日消灭煞", "日山方煞"),
    "安葬": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "月正阴府", "日正阴府", "时正阴府", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁", "日消灭煞", "日山方煞"),
    "附葬": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "月正阴府", "日正阴府", "时正阴府", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁", "日消灭煞", "日山方煞"),
    "修坟": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日星曜煞", "时星曜煞", "天星煞", "地曜煞"),
    "旧坟立碑": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日星曜煞", "时星曜煞", "天星煞", "地曜煞"),
    "安葬破土": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀"),
    "附葬破土": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀"),
    "造坟": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "月正阴府", "日正阴府", "时正阴府", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁", "日消灭煞", "日山方煞"),
    "启攒": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀"),
    "移香出火": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁"),
    "入宅归火": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀", "日正八煞", "时正八煞", "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁"),
    "拆卸": ("月冲山", "日冲山", "时冲山"),
    "避宅修方": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀"),
    "避宅装修": ("月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀"),
    "空方动土": (),
    "其它": (),
    "交易": (),
}

def _use_meta(label: str) -> dict:
    mountain_title = "第二步【选择坐山】"
    if label in {"附葬", "修方兼竖造"}:
        mountain_title = "第二步【选择新坐山】"
    if label in {"安门", "造门楼"}:
        mountain_title = "第二步【选择门向】"
    if label == "旧坟立碑":
        mountain_title = "第二步【选择碑向】"

    life_name = "福主年命"
    if label in BURIAL_USE_TYPES:
        life_name = "祭主年命"
    if label == "作灶":
        life_name = "馈主年命"

    return {
        "code": USE_TYPE_CODE[label],
        "label": label,
        "show_mountain": label not in NO_MOUNTAIN_USE_TYPES,
        "show_repair": label in REPAIR_USE_TYPES,
        "show_deceased": label in BURIAL_USE_TYPES,
        "show_year_sha": label not in NO_MOUNTAIN_USE_TYPES,
        "mountain_mode": "facing" if label in FACING_USE_TYPES else "sitting",
        "mountain_title": mountain_title,
        "life_name": life_name,
        "auto_repair": (
            "seat_facing" if label == "旧坟立碑"
            else "seat" if label in AUTO_SEAT_REPAIR_USE_TYPES
            else ""
        ),
        "month_mode": "relation" if label in WANGSHENG_MONTH_USE_TYPES else "mountain",
        "default_month_relations": list(REFERENCE_MONTH_RELATIONS.get(label, ())) if label in WANGSHENG_MONTH_USE_TYPES else [],
        "default_sha_filters": list(REFERENCE_SHA_FILTERS.get(label, ())),
    }

USE_META = {label: _use_meta(label) for label in USE_TYPES}

# 原站 topzeri.js 的 yijixuanze()/yijixuanze1()。
# 这两个字段不是“宜事加分”，而是“排除日忌”：当天通书“忌”中命中任一项就直接排除。
REFERENCE_DAY_JI_FILTERS_XIEJI = {
    "建造": ("竖造",),
    "进神": ("入宅", "安香火"),
    "安门": ("安门",),
    "修方兼竖造": ("竖造",),
    "修方": ("修造",),
    "装修": ("修造",),
    "入宅": ("入宅",),
    "造门楼": ("修造", "动土"),
    "竖造动土": ("动土",),
    "修方动土": ("修造", "动土"),
    "开业": ("开业",),
    "作灶": ("作灶",),
    "封顶上樑": ("上梁",),
    "升层": ("修造",),
    "安葬": ("安葬",),
    "附葬": ("安葬",),
    "修坟": ("修造", "动土"),
    "旧坟立碑": ("修造", "动土"),
    "安葬破土": ("破土",),
    "附葬破土": ("破土", "修造"),
    "造坟": ("竖造",),
    "启攒": ("启攒",),
    "移香出火": ("安香火",),
    "入宅归火": ("入宅", "安香火"),
    "拆卸": ("拆卸", "动土"),
    "避宅修方": ("修造",),
    "避宅装修": ("修造",),
    "空方动土": ("动土",),
    "其它": (),
    "交易": ("交易",),
}

REFERENCE_DAY_JI_FILTERS_TONGSHU = {
    **REFERENCE_DAY_JI_FILTERS_XIEJI,
    # 原站 yijixuanze1() 唯一可见差异：通书版“拆卸”不再额外排除“动土”。
    "拆卸": ("拆卸",),
}

REFERENCE_EDITIONS = {
    "协纪版": REFERENCE_DAY_JI_FILTERS_XIEJI,
    "通书版": REFERENCE_DAY_JI_FILTERS_TONGSHU,
}

HOUR_OPTIONS = [
    {"hour": 0, "zhi": "子", "label": "子时"},
    {"hour": 2, "zhi": "丑", "label": "丑时"},
    {"hour": 4, "zhi": "寅", "label": "寅时"},
    {"hour": 6, "zhi": "卯", "label": "卯时"},
    {"hour": 8, "zhi": "辰", "label": "辰时"},
    {"hour": 10, "zhi": "巳", "label": "巳时"},
    {"hour": 12, "zhi": "午", "label": "午时"},
    {"hour": 14, "zhi": "未", "label": "未时"},
    {"hour": 16, "zhi": "申", "label": "申时"},
    {"hour": 18, "zhi": "酉", "label": "酉时"},
    {"hour": 20, "zhi": "戌", "label": "戌时"},
    {"hour": 22, "zhi": "亥", "label": "亥时"},
]


@dataclass(frozen=True)
class Mountain:
    id: int
    trigram_id: int
    trigram: str
    direction: str
    name: str
    element: str


# 编号、方位和五行来自目标站点 topzeri.js 的 selects 数组。
_MOUNTAIN_ROWS = [
    (1, 1, "坎", "正北偏右", "壬", "水"),
    (2, 1, "坎", "正北居中", "子", "水"),
    (3, 1, "坎", "正北偏左", "癸", "水"),
    (4, 8, "艮", "东北偏右", "丑", "土"),
    (5, 8, "艮", "东北居中", "艮", "土"),
    (6, 8, "艮", "东北偏左", "寅", "木"),
    (7, 3, "震", "正东偏右", "甲", "木"),
    (8, 3, "震", "正东居中", "卯", "木"),
    (9, 3, "震", "正东偏左", "乙", "木"),
    (10, 4, "巽", "东南偏右", "辰", "土"),
    (11, 4, "巽", "东南居中", "巽", "木"),
    (12, 4, "巽", "东南偏左", "巳", "火"),
    (13, 9, "离", "正南偏右", "丙", "火"),
    (14, 9, "离", "正南居中", "午", "火"),
    (15, 9, "离", "正南偏左", "丁", "火"),
    (16, 2, "坤", "西南偏右", "未", "土"),
    (17, 2, "坤", "西南居中", "坤", "土"),
    (18, 2, "坤", "西南偏左", "申", "金"),
    (19, 7, "兑", "正西偏右", "庚", "金"),
    (20, 7, "兑", "正西居中", "酉", "金"),
    (21, 7, "兑", "正西偏左", "辛", "金"),
    (22, 6, "乾", "西北偏右", "戌", "土"),
    (23, 6, "乾", "西北居中", "乾", "金"),
    (24, 6, "乾", "西北偏左", "亥", "水"),
]
MOUNTAINS = {r[0]: Mountain(*r) for r in _MOUNTAIN_ROWS}
MOUNTAIN_ORDER = [MOUNTAINS[i].name for i in range(1, 25)]
MOUNTAIN_ID_BY_NAME = {m.name: m.id for m in MOUNTAINS.values()}

OPPOSITE_MOUNTAIN = {
    MOUNTAIN_ORDER[i]: MOUNTAIN_ORDER[(i + 12) % 24] for i in range(24)
}

# 120分金在目标站点中按24山映射到相邻十二地支，每支五个分金。
FENJIN_ZHI_BY_MOUNTAIN_ID = {
    1: "亥", 2: "子", 3: "子", 4: "丑", 5: "丑", 6: "寅",
    7: "寅", 8: "卯", 9: "卯", 10: "辰", 11: "辰", 12: "巳",
    13: "巳", 14: "午", 15: "午", 16: "未", 17: "未", 18: "申",
    19: "申", 20: "酉", 21: "酉", 22: "戌", 23: "戌", 24: "亥",
}

# 网站 topzeri.js 的 arraydagua，按二十四山直接映射。
DAGUA_OPTIONS = {
    1: (("风地观", "2;2"), ("水地比", "7;7"), ("山地剥", "6;6")),
    2: (("山地剥", "6;6"), ("坤为地", "1;1"), ("地雷复", "1;8"), ("山雷颐", "6;3")),
    3: (("山雷颐", "6;3"), ("水雷屯", "7;4"), ("风雷益", "2;9")),
    4: (("震为雷", "8;1"), ("火雷噬嗑", "3;6"), ("泽雷随", "4;7")),
    5: (("泽雷随", "4;7"), ("天雷无妄", "9;2"), ("地火明夷", "1;3"), ("山火贲", "6;8")),
    6: (("山火贲", "6;8"), ("水火既济", "7;9"), ("风火家人", "2;4")),
    7: (("雷火丰", "8;6"), ("离为火", "3;1"), ("泽火革", "4;2")),
    8: (("泽火革", "4;2"), ("天火同人", "9;7"), ("地泽临", "1;4"), ("山泽损", "6;9")),
    9: (("山泽损", "6;9"), ("水泽节", "7;8"), ("风泽中孚", "2;3")),
    10: (("雷泽归妹", "8;7"), ("火泽睽", "3;2"), ("兑为泽", "4;1")),
    11: (("兑为泽", "4;1"), ("天泽履", "9;6"), ("地天泰", "1;9"), ("山天大畜", "6;4")),
    12: (("山天大畜", "6;4"), ("水天需", "7;3"), ("风天小畜", "2;8")),
    13: (("雷天大壮", "8;2"), ("火天大有", "3;7"), ("泽天夬", "4;6")),
    14: (("泽天夬", "4;6"), ("乾为天", "9;1"), ("天风姤", "9;5"), ("泽风大过", "4;3")),
    15: (("泽风大过", "4;3"), ("火风鼎", "3;4"), ("雷风恒", "8;9")),
    16: (("巽为风", "2;1"), ("水风井", "7;6"), ("山风蛊", "6;7")),
    17: (("山风蛊", "6;7"), ("地风升", "1;2"), ("天水讼", "9;3"), ("泽水困", "4;8")),
    18: (("泽水困", "4;8"), ("火水未济", "3;9"), ("雷水解", "8;4")),
    19: (("风水涣", "2;6"), ("坎为水", "7;1"), ("山水蒙", "6;2")),
    20: (("山水蒙", "6;2"), ("地水师", "1;7"), ("天山遁", "9;4"), ("泽山咸", "4;9")),
    21: (("泽山咸", "4;9"), ("火山旅", "3;8"), ("雷山小过", "8;3")),
    22: (("风山渐", "2;7"), ("水山蹇", "7;2"), ("艮为山", "6;1")),
    23: (("艮为山", "6;1"), ("地山谦", "1;6"), ("天地否", "9;6"), ("泽地萃", "4;4")),
    24: (("泽地萃", "4;4"), ("火地晋", "3;3"), ("雷地豫", "8;8")),
}
YANG_ZHI = set("子寅辰午申戌")


def _jian_options(mountain_id: int) -> list[dict]:
    idx = mountain_id - 1
    right = MOUNTAIN_ORDER[(idx - 1) % 24]
    left = MOUNTAIN_ORDER[(idx + 1) % 24]
    return [
        {"value": right + OPPOSITE_MOUNTAIN[right], "label": f"兼右【{right}{OPPOSITE_MOUNTAIN[right]}】"},
        {"value": "正针", "label": "【正针】"},
        {"value": left + OPPOSITE_MOUNTAIN[left], "label": f"兼左【{left}{OPPOSITE_MOUNTAIN[left]}】"},
    ]


def _fenjin_options(mountain_id: int) -> list[str]:
    zhi = FENJIN_ZHI_BY_MOUNTAIN_ID[mountain_id]
    stems = "甲丙戊庚壬" if zhi in YANG_ZHI else "乙丁己辛癸"
    return [f"{gan}{zhi}" for gan in stems]


def _facing_direction(direction: str) -> str:
    if "偏右" in direction:
        return direction.replace("偏右", "偏左")
    if "偏左" in direction:
        return direction.replace("偏左", "偏右")
    return direction


def _mountain_cardinal(mountain: Mountain) -> str | None:
    if mountain.direction.startswith("正北"):
        return "北"
    if mountain.direction.startswith("正南"):
        return "南"
    if mountain.direction.startswith("正东"):
        return "东"
    if mountain.direction.startswith("正西"):
        return "西"
    return None


def _is_sansha_for_mountain(branch: str, mountain: Mountain) -> bool:
    """Match the reference default 月/日/时三杀 hard filter."""
    cardinal = _mountain_cardinal(mountain)
    return bool(cardinal and SAN_SHA_DIRECTION.get(branch) == cardinal)


def _day_relation(day_element: str, mountain_element: str) -> tuple[str, int]:
    # 以山家为主体：同我为旺，日干生山为生，山生日干为泄，
    # 山克日干为耗，日干克山为克。对应目标站点“旺/生/耗/泄/克”筛选项。
    if day_element == mountain_element:
        return "旺", 4
    if GENERATES[day_element] == mountain_element:
        return "生", 3
    if GENERATES[mountain_element] == day_element:
        return "泄", 0
    if CONTROLS[mountain_element] == day_element:
        return "耗", 1
    return "克", -4


def _safe_list(obj, method_name: str) -> list[str]:
    method = getattr(obj, method_name, None)
    if not callable(method):
        return []
    try:
        value = method()
    except Exception:
        return []
    return [str(v) for v in (value or [])]


def _life_ganzhi(value: str | int) -> str | None:
    text = str(value).strip()
    if not text:
        return None
    if len(text) >= 2 and text[0] in GAN and text[1] in ZHI:
        return text[:2]
    try:
        year = int(text)
    except ValueError:
        return None
    if year < 1 or year > 9999:
        return None
    # 用年中日期取干支，避开立春前后边界。年命输入本身只给年份时，这是可重复的映射。
    lunar = Solar.fromYmd(year, 7, 1).getLunar()
    return lunar.getYearInGanZhiExact()


def _same_san_he(a: str, b: str) -> bool:
    return any(a in group and b in group for group in SAN_HE)


def _reference_day_ji_filters(use_type: str, edition: str) -> tuple[str, ...]:
    table = REFERENCE_EDITIONS.get(edition, REFERENCE_DAY_JI_FILTERS_XIEJI)
    return tuple(table.get(use_type, ()))


def _is_excluded_by_day_ji(use_type: str, edition: str, day_ji: Iterable[str]) -> tuple[bool, list[str]]:
    ji = set(str(x) for x in day_ji)
    hits = [item for item in _reference_day_ji_filters(use_type, edition) if item in ji]
    return bool(hits), hits


def _hour_rows(d: date, hours: list[int], mountain: Mountain) -> list[dict]:
    rows = []
    for hour in hours:
        solar = Solar.fromYmdHms(d.year, d.month, d.day, hour, 0, 0)
        ec = solar.getLunar().getEightChar()
        gz = ec.getTime()
        element = GAN_ELEMENT.get(ec.getTimeGan(), "")
        relation, rel_score = _day_relation(element, mountain.element)
        rows.append({
            "hour": hour,
            "zhi": ec.getTimeZhi(),
            "ganzhi": gz,
            "relation": relation,
            "recommended": rel_score >= 1,
        })
    return rows


def _grade(score: int, fatal: bool) -> tuple[int, str]:
    if fatal:
        return 0, "不取"
    if score >= 8:
        return 1, "1级大吉"
    if score >= 5:
        return 2, "2级小吉"
    if score >= 2:
        return 3, "3级日干生旺"
    return 4, "4级日干次旺"


def _passes_level(level: int, filter_name: str, day_relation: str) -> bool:
    # 原站 paichubiaozhi 中“生旺/耗”是日干对山家的独立五行分类，
    # 不是 1~4 级的累计阈值。黑盒样本已确认：壬山“生旺”只出现
    # 庚辛壬癸日，“耗”只出现丙丁日。
    if filter_name == "全部":
        return True
    if filter_name == "生旺":
        return day_relation in {"生", "旺"}
    if filter_name == "耗":
        return day_relation == "耗"
    if filter_name == "大吉":
        return level == 1
    if filter_name == "小吉":
        return level == 2
    return True


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def get_options() -> dict:
    mountains = []
    for mountain_id in range(1, 25):
        m = MOUNTAINS[mountain_id]
        mountains.append({
            "id": m.id,
            "trigram_id": m.trigram_id,
            "trigram": m.trigram,
            "direction": m.direction,
            "name": m.name,
            "element": m.element,
            "label": f"{m.direction}【{m.name}山】{m.element}",
            "facing_direction": _facing_direction(m.direction),
            "facing_label": f"{_facing_direction(m.direction)}【{m.name}向】{m.element}",
            "jian": _jian_options(m.id),
            "fenjin": _fenjin_options(m.id),
            "dagua": [{"label": label, "value": value} for label, value in DAGUA_OPTIONS[m.id]],
            "auto_favorable_months": list(MOUNTAIN_FAVORABLE_MONTHS[m.id]),
        })
    return {
        "mountains": mountains,
        "trigrams": TRIGRAM_OPTIONS,
        "repair_directions": [{"label": label, "value": value} for label, value in REPAIR_DIRECTION_BUTTONS],
        "repair_positions": REPAIR_POSITIONS,
        "use_types": USE_TYPES,
        "use_type_options": [{"value": code, "label": label} for code, label in USE_TYPE_OPTIONS],
        "use_meta": USE_META,
        "default_sha_filters": {k: list(v) for k, v in REFERENCE_SHA_FILTERS.items()},
        "editions": list(REFERENCE_EDITIONS),
        "day_ji_filters": {
            edition: {k: list(v) for k, v in table.items()}
            for edition, table in REFERENCE_EDITIONS.items()
        },
        "levels": [
            {"value": "全部", "label": "全部"},
            {"value": "大吉", "label": "1级大吉"},
            {"value": "小吉", "label": "2级小吉"},
            {"value": "生旺", "label": "3级日干生旺"},
            {"value": "耗", "label": "4级日干次旺"},
        ],
        "hours": HOUR_OPTIONS,
        "month_favorable": {k: sorted(v) for k, v in MONTH_ELEMENT_FAVORABLE.items()},
    }


def calculate_days(payload: dict) -> dict:
    mountain_id = int(payload.get("mountain_id", 1))
    if mountain_id not in MOUNTAINS:
        raise ValueError("无效的二十四山编号")
    mountain = MOUNTAINS[mountain_id]

    use_type = str(payload.get("use_type", "建造"))
    if use_type not in USE_TYPES:
        raise ValueError("无效的用事类型")
    edition = str(payload.get("edition", "协纪版"))
    if edition not in REFERENCE_EDITIONS:
        raise ValueError("无效的宜忌版本")

    start = _parse_date(str(payload["start_date"]))
    end = _parse_date(str(payload["end_date"]))
    if end < start:
        raise ValueError("结束日期不能早于开始日期")
    if (end - start).days > 420:
        raise ValueError("一次最多计算421天")

    ganzhi_year_filter = str(payload.get("ganzhi_year", "")).strip()
    ganzhi_month_filter = str(payload.get("ganzhi_month", "")).strip()
    ganzhi_day_filter = str(payload.get("ganzhi_day_filter", "")).strip()

    level_filter = str(payload.get("level", "大吉"))
    selected_months = {str(x) for x in payload.get("favorable_months", []) if str(x) in ZHI}
    raw_month_relations = payload.get("month_relations", [])
    if isinstance(raw_month_relations, str):
        raw_month_relations = [x for x in re.split(r"[;,，\s]+", raw_month_relations) if x]
    selected_month_relations = {str(x) for x in raw_month_relations if str(x) in {"旺", "生", "耗", "泄", "克"}}
    if use_type in WANGSHENG_MONTH_USE_TYPES and not selected_month_relations:
        selected_month_relations = set(REFERENCE_MONTH_RELATIONS.get(use_type, ()))

    raw_hours = payload.get("hours") or [item["hour"] for item in HOUR_OPTIONS]
    hours = sorted({int(h) for h in raw_hours if int(h) in range(0, 24, 2)})
    if not hours:
        hours = [item["hour"] for item in HOUR_OPTIONS]

    life_inputs = payload.get("life_years", [])
    if isinstance(life_inputs, str):
        life_inputs = [x.strip() for x in life_inputs.replace("，", ",").split(",") if x.strip()]
    life_ganzhi = [g for g in (_life_ganzhi(x) for x in life_inputs) if g]

    deceased_inputs = payload.get("deceased_years", [])
    if isinstance(deceased_inputs, str):
        deceased_inputs = [x.strip() for x in deceased_inputs.replace("，", ",").split(",") if x.strip()]
    deceased_ganzhi = [g for g in (_life_ganzhi(x) for x in deceased_inputs) if g]

    repair_positions = [str(x) for x in payload.get("repair_positions", []) if str(x)]
    dagua = str(payload.get("dagua", ""))
    dagua_value = str(payload.get("dagua_value", ""))

    results = []
    current = start
    while current <= end:
        lunar = Solar.fromYmd(current.year, current.month, current.day).getLunar()
        eight = lunar.getEightChar()

        year_gz = eight.getYear()
        month_gz = eight.getMonth()
        day_gz = eight.getDay()
        year_zhi = eight.getYearZhi()
        month_zhi = eight.getMonthZhi()
        day_zhi = eight.getDayZhi()
        day_gan = eight.getDayGan()
        day_element = GAN_ELEMENT[day_gan]

        if ganzhi_year_filter and year_gz != ganzhi_year_filter:
            current += timedelta(days=1)
            continue
        if ganzhi_month_filter and month_gz != ganzhi_month_filter:
            current += timedelta(days=1)
            continue
        if ganzhi_day_filter and ganzhi_day_filter != "全部":
            if ganzhi_day_filter in GAN and day_gan != ganzhi_day_filter:
                current += timedelta(days=1)
                continue
            if ganzhi_day_filter in ZHI and day_zhi != ganzhi_day_filter:
                current += timedelta(days=1)
                continue

        if selected_months and month_zhi not in selected_months:
            current += timedelta(days=1)
            continue

        # 原站默认凶煞过滤包含“月三杀、日三杀、时三杀”，但不包含“年三杀”。
        # 因此年三杀只显示提示；月/日/时三杀会把候选日课直接排除。
        if _is_sansha_for_mountain(month_zhi, mountain):
            current += timedelta(days=1)
            continue
        if _is_sansha_for_mountain(day_zhi, mountain):
            current += timedelta(days=1)
            continue

        month_relation, _ = _day_relation(ZHI_ELEMENT[month_zhi], mountain.element)
        if use_type in WANGSHENG_MONTH_USE_TYPES and selected_month_relations and month_relation not in selected_month_relations:
            current += timedelta(days=1)
            continue

        score = 0
        fatal = False
        good: list[str] = []
        bad: list[str] = []

        relation, rel_score = _day_relation(day_element, mountain.element)
        score += rel_score
        if rel_score >= 2:
            good.append(f"日干{day_gan}{day_element}对{mountain.name}山{mountain.element}为{relation}")
        elif rel_score < 0:
            bad.append(f"日干{day_gan}{day_element}克山家{mountain.element}")
        else:
            good.append(f"日干与山家关系：{relation}")

        if use_type in WANGSHENG_MONTH_USE_TYPES:
            if month_relation in {"旺", "生"}:
                score += 3
            elif month_relation == "耗":
                score += 1
            good.append(f"{month_zhi}月对{mountain.name}山为{month_relation}")
        else:
            auto_months = MOUNTAIN_FAVORABLE_MONTHS[mountain.id]
            if month_zhi in auto_months:
                score += 3
                good.append(f"{month_zhi}月在{mountain.name}山自动利月表内")
            else:
                score -= 1
                bad.append(f"{month_zhi}月不在{mountain.name}山自动利月表内")

        if mountain.name in ZHI and CLASH[day_zhi] == mountain.name:
            score -= 8
            fatal = True
            bad.append(f"{day_zhi}日冲{mountain.name}山")

        if mountain.name in ZHI and CLASH[year_zhi] == mountain.name:
            score -= 5
            bad.append(f"{year_zhi}年与{mountain.name}山相冲")

        cardinal = _mountain_cardinal(mountain)
        san_sha = SAN_SHA_DIRECTION.get(year_zhi)
        if cardinal and san_sha == cardinal:
            score -= 6
            bad.append(f"{year_zhi}年三煞在{san_sha}方")

        for life in life_ganzhi:
            life_zhi = life[1]
            if CLASH[day_zhi] == life_zhi:
                score -= 3
                bad.append(f"日支{day_zhi}冲福主年命{life}")
            elif LIU_HE[day_zhi] == life_zhi:
                score += 1
                good.append(f"日支{day_zhi}与福主年命{life}六合")
            elif _same_san_he(day_zhi, life_zhi):
                score += 1
                good.append(f"日支{day_zhi}与福主年命{life}三合局")

        day_yi = _safe_list(lunar, "getDayYi")
        day_ji = _safe_list(lunar, "getDayJi")
        excluded_by_ji, ji_hits = _is_excluded_by_day_ji(use_type, edition, day_ji)
        if excluded_by_ji:
            current += timedelta(days=1)
            continue

        tian_shen_type = ""
        method = getattr(lunar, "getDayTianShenType", None)
        if callable(method):
            try:
                tian_shen_type = str(method())
            except Exception:
                tian_shen_type = ""
        if "黄道" in tian_shen_type:
            score += 1
            good.append("黄道日")
        elif "黑道" in tian_shen_type:
            score -= 1
            bad.append("黑道日")

        level, level_name = _grade(score, fatal)
        if _passes_level(level, level_filter, relation):
            # 原站一个“日课”对应一个具体日期+时辰，而不是一天一个结果。
            # 因此把所选时辰展开为独立 lesson；这也让顶部时辰勾选与
            # “显示：N个日课”计数语义和原站一致。
            for hour_row in _hour_rows(current, hours, mountain):
                if _is_sansha_for_mountain(hour_row["zhi"], mountain):
                    continue
                results.append({
                    "lesson_id": f"{current.strftime('%Y%m%d')}{int(hour_row['hour']):02d}",
                    "date": current.isoformat(),
                    "hour": hour_row["hour"],
                    "time_zhi": hour_row["zhi"],
                    "time_ganzhi": hour_row["ganzhi"],
                    "time_relation": hour_row["relation"],
                    "lunar": lunar.toString(),
                    "year_ganzhi": year_gz,
                    "month_ganzhi": month_gz,
                    "day_ganzhi": day_gz,
                    "month_zhi": month_zhi,
                    "day_element": day_element,
                    "relation": relation,
                    "score": score,
                    "level": level,
                    "level_name": level_name,
                    "good": list(good),
                    "bad": list(bad),
                    "yi": day_yi,
                    "ji": day_ji,
                    "hours": [hour_row],
                })

        current += timedelta(days=1)

    results.sort(key=lambda item: (item["date"], item["hour"]))

    return {
        "mountain": {
            "id": mountain.id,
            "name": mountain.name,
            "element": mountain.element,
            "trigram": mountain.trigram,
            "direction": mountain.direction,
            "opposite": OPPOSITE_MOUNTAIN[mountain.name],
            "jian_options": _jian_options(mountain.id),
            "fenjin_options": _fenjin_options(mountain.id),
        },
        "use_type": use_type,
        "edition": edition,
        "day_ji_filters": list(_reference_day_ji_filters(use_type, edition)),
        "sha_filters": list(REFERENCE_SHA_FILTERS.get(use_type, ())),
        "calendar_filter": {
            "ganzhi_year": ganzhi_year_filter,
            "ganzhi_month": ganzhi_month_filter,
            "ganzhi_day_filter": ganzhi_day_filter,
        },
        "life_ganzhi": life_ganzhi,
        "deceased_ganzhi": deceased_ganzhi,
        "repair_positions": repair_positions,
        "dagua": dagua,
        "dagua_value": dagua_value,
        "month_relations": sorted(selected_month_relations),
        "count": len(results),
        "results": results,
        "rule_notes": [
            "二十四山编号/方位/五行、兼山结构、120分金结构与目标站点前端数据一致。",
            "利月按目标站点公开的寅卯木火、辰土金、巳午火土、未土、申酉金水、戌土金、亥子水木、丑土金规则。",
            "每个结果按“日期+时辰”作为一个日课；默认按原站启用月三杀、日三杀、时三杀硬过滤，年三杀仅显示不排除。",
        ],
    }
