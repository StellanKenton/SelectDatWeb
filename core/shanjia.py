from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable

from lunar_python import Solar


GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

GAN_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
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

# 网站 topzeri_info.php 中可见的“手动添加利月”规则。
MONTH_FAVORABLE = {
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

# 原站 topzeri.js 的“自动添加利月”并非单纯按五行统一映射，而是逐山固定表。
# 下表按原站 1..24 山编号逐项复刻。
AUTO_FAVORABLE_MONTHS = {
    1: ("申", "酉", "亥", "子"), 2: ("申", "酉", "亥", "子"), 3: ("申", "酉", "亥", "子"),
    4: ("巳", "辰", "丑"), 5: ("巳", "午", "辰", "未", "戌", "丑"), 6: ("寅", "卯", "亥", "子"),
    7: ("寅", "卯", "亥", "子"), 8: ("寅", "卯", "亥", "子"), 9: ("寅", "卯", "亥", "子"),
    10: ("巳", "午", "辰", "未"), 11: ("寅", "卯", "亥", "子"), 12: ("寅", "卯", "巳", "午"),
    13: ("寅", "卯", "巳", "午"), 14: ("寅", "卯", "巳", "午"), 15: ("寅", "卯", "巳", "午"),
    16: ("巳", "午", "未", "戌"), 17: ("巳", "午", "辰", "未", "戌", "丑"),
    18: ("申", "酉", "辰", "戌", "丑"), 19: ("申", "酉", "辰", "戌", "丑"),
    20: ("申", "酉", "辰", "戌", "丑"), 21: ("申", "酉", "辰", "戌", "丑"),
    22: ("巳", "午", "戌"), 23: ("申", "酉", "辰", "戌", "丑"), 24: ("申", "酉", "亥", "子"),
}

# 原站 topzeri.js 的逐山玄空大卦选项，value 保留原站“卦数;运数”格式。
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

# 三煞方：申子辰年煞南、寅午戌年煞北、亥卯未年煞西、巳酉丑年煞东。
SAN_SHA_DIRECTION = {
    "申": "南", "子": "南", "辰": "南",
    "寅": "北", "午": "北", "戌": "北",
    "亥": "西", "卯": "西", "未": "西",
    "巳": "东", "酉": "东", "丑": "东",
}

USE_TYPES = [
    "建造", "进神", "安门", "修方兼竖造", "修方", "装修", "入宅", "造门楼",
    "竖造动土", "修方动土", "开业", "作灶", "封顶上樑", "升层", "安葬",
    "附葬", "修坟", "旧坟立碑", "安葬破土", "附葬破土", "造坟", "启攒",
    "移香出火", "入宅归火", "拆卸", "避宅修方", "避宅装修", "空方动土",
    "其它", "交易",
]

USE_TYPE_YI_ALIASES = {
    "建造": ("修造", "竖造", "动土"),
    "进神": ("祭祀", "祈福"),
    "安门": ("安门",),
    "修方兼竖造": ("修造", "动土", "竖造"),
    "修方": ("修造",),
    "装修": ("修造",),
    "入宅": ("入宅",),
    "造门楼": ("安门", "修造"),
    "竖造动土": ("竖造", "动土"),
    "修方动土": ("修造", "动土"),
    "开业": ("开市", "开业", "交易"),
    "作灶": ("作灶",),
    "封顶上樑": ("上梁", "竖柱"),
    "升层": ("修造", "竖造"),
    "安葬": ("安葬",),
    "附葬": ("安葬",),
    "修坟": ("修坟", "修造"),
    "旧坟立碑": ("立碑", "修坟"),
    "安葬破土": ("安葬", "破土"),
    "附葬破土": ("安葬", "破土"),
    "造坟": ("安葬", "破土"),
    "启攒": ("启攒",),
    "移香出火": ("出火", "移徙"),
    "入宅归火": ("入宅", "出火"),
    "拆卸": ("拆卸",),
    "避宅修方": ("修造",),
    "避宅装修": ("修造",),
    "空方动土": ("动土",),
    "交易": ("交易", "立券"),
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


def _match_use_type(use_type: str, day_yi: Iterable[str], day_ji: Iterable[str]) -> tuple[int, list[str]]:
    aliases = USE_TYPE_YI_ALIASES.get(use_type, (use_type,))
    yi_text = "、".join(day_yi)
    ji_text = "、".join(day_ji)
    reasons: list[str] = []
    score = 0
    yi_hits = [x for x in aliases if x and x in yi_text]
    ji_hits = [x for x in aliases if x and x in ji_text]
    if yi_hits:
        score += 2
        reasons.append("宜：" + "、".join(yi_hits))
    if ji_hits:
        score -= 4
        reasons.append("忌：" + "、".join(ji_hits))
    return score, reasons


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


def _passes_level(level: int, filter_name: str) -> bool:
    if filter_name == "全部":
        return True
    if level == 0:
        return False
    max_level = {"大吉": 1, "小吉": 2, "生旺": 3, "耗": 4}.get(filter_name, 4)
    return level <= max_level


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
            "jian": _jian_options(m.id),
            "fenjin": _fenjin_options(m.id),
            "dagua": [{"name": name, "value": value} for name, value in DAGUA_OPTIONS[m.id]],
            "favorable_months": list(AUTO_FAVORABLE_MONTHS[m.id]),
        })
    return {
        "mountains": mountains,
        "use_types": USE_TYPES,
        "levels": [
            {"value": "全部", "label": "全部"},
            {"value": "大吉", "label": "1级大吉"},
            {"value": "小吉", "label": "2级小吉"},
            {"value": "生旺", "label": "3级日干生旺"},
            {"value": "耗", "label": "4级日干次旺"},
        ],
        "hours": HOUR_OPTIONS,
        "month_favorable": {k: sorted(v) for k, v in MONTH_FAVORABLE.items()},
    }


def calculate_days(payload: dict) -> dict:
    mountain_id = int(payload.get("mountain_id", 1))
    if mountain_id not in MOUNTAINS:
        raise ValueError("无效的二十四山编号")
    mountain = MOUNTAINS[mountain_id]

    use_type = str(payload.get("use_type", "建造"))
    if use_type not in USE_TYPES:
        raise ValueError("无效的用事类型")

    start = _parse_date(str(payload["start_date"]))
    end = _parse_date(str(payload["end_date"]))
    if end < start:
        raise ValueError("结束日期不能早于开始日期")
    if (end - start).days > 366:
        raise ValueError("一次最多计算367天")

    level_filter = str(payload.get("level", "小吉"))
    selected_months = {str(x) for x in payload.get("favorable_months", []) if str(x) in ZHI}

    raw_hours = payload.get("hours") or [item["hour"] for item in HOUR_OPTIONS]
    hours = sorted({int(h) for h in raw_hours if int(h) in range(0, 24, 2)})
    if not hours:
        hours = [item["hour"] for item in HOUR_OPTIONS]

    life_inputs = payload.get("life_years", [])
    if isinstance(life_inputs, str):
        life_inputs = [x.strip() for x in life_inputs.replace("，", ",").split(",") if x.strip()]
    life_ganzhi = [g for g in (_life_ganzhi(x) for x in life_inputs) if g]

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

        if selected_months and month_zhi not in selected_months:
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

        if month_zhi in AUTO_FAVORABLE_MONTHS[mountain.id]:
            score += 3
            good.append(f"{month_zhi}月在{mountain.name}山自动利月表")
        else:
            score -= 1
            bad.append(f"{month_zhi}月不在{mountain.name}山自动利月表")

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
        use_score, use_reasons = _match_use_type(use_type, day_yi, day_ji)
        score += use_score
        for reason in use_reasons:
            (bad if reason.startswith("忌：") else good).append(reason)

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
        if _passes_level(level, level_filter):
            results.append({
                "date": current.isoformat(),
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
                "good": good,
                "bad": bad,
                "yi": day_yi,
                "ji": day_ji,
                "hours": _hour_rows(current, hours, mountain),
            })

        current += timedelta(days=1)

    results.sort(key=lambda item: (
        9 if item["level"] == 0 else item["level"],
        -item["score"],
        item["date"],
    ))

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
            "dagua_options": [{"name": name, "value": value} for name, value in DAGUA_OPTIONS[mountain.id]],
            "favorable_months": list(AUTO_FAVORABLE_MONTHS[mountain.id]),
            "selected_jian": str(payload.get("jian", "")),
            "selected_fenjin": str(payload.get("fenjin", "")),
            "selected_dagua": str(payload.get("dagua", "")),
        },
        "use_type": use_type,
        "life_ganzhi": life_ganzhi,
        "count": len(results),
        "results": results,
        "rule_notes": [
            "二十四山编号/方位/五行、兼山结构、120分金结构与目标站点前端数据一致。",
            "自动利月按目标站 topzeri.js 的 24 山逐山固定表计算；手动利月菜单仍保留原站按五行说明。",
            "日课等级由可公开确认的五行、利月、冲合、年三煞、通胜宜忌组合计算；目标站点服务端未公开的私有权重不做伪造。",
        ],
    }
