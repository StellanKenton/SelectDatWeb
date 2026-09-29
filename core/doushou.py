"""斗首五神与十二长生排盘。

五类山位和五神番化先由原站壬、丙、甲、艮、庚的可见卡片核对。
其余山位按同一斗首五行组推演，保留独立样本验证的边界。
"""

from __future__ import annotations


MOUNTAIN_ELEMENT = {
    **dict.fromkeys("壬子巽巳辛戌", "土"),
    **dict.fromkeys("艮寅丁未", "木"),
    **dict.fromkeys("癸丑丙午乾亥", "火"),
    **dict.fromkeys("坤申甲卯", "水"),
    **dict.fromkeys("乙庚辰酉", "金"),
}
STEM_ELEMENT = {
    **dict.fromkeys("甲己", "土"),
    **dict.fromkeys("乙庚", "金"),
    **dict.fromkeys("丙辛", "水"),
    **dict.fromkeys("丁壬", "木"),
    **dict.fromkeys("戊癸", "火"),
}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
TRANSFORM = {"元": "元", "武": "贪", "贪": "破", "破": "廉", "廉": "武"}
STAGES = "长沐冠临帝衰病死墓绝胎养"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
LONG_LIFE_START = {"木": "亥", "火": "寅", "土": "申", "金": "巳", "水": "申"}


def star_for(mountain_element: str, stem_element: str) -> str:
    if stem_element == mountain_element:
        return "元"
    if GENERATES[mountain_element] == stem_element:
        return "廉"
    if GENERATES[stem_element] == mountain_element:
        return "贪"
    if CONTROLS[mountain_element] == stem_element:
        return "武"
    if CONTROLS[stem_element] == mountain_element:
        return "破"
    raise ValueError("无效的斗首五行")


def element_for_star(mountain_element: str, star: str) -> str:
    return next(element for element in GENERATES if star_for(mountain_element, element) == star)


def long_life(element: str, branch: str) -> str:
    start = BRANCHES.index(LONG_LIFE_START[element])
    return STAGES[(BRANCHES.index(branch) - start) % 12]


def calculate_doushou(mountain: str, pillars: tuple[str, str, str, str]) -> dict:
    element = MOUNTAIN_ELEMENT[mountain]
    rows = []
    for ganzhi in pillars:
        stem, branch = ganzhi
        upper_element = STEM_ELEMENT[stem]
        upper_star = star_for(element, upper_element)
        lower_star = TRANSFORM[upper_star]
        rows.append({
            "ganzhi": ganzhi,
            "upper_star": upper_star,
            "upper_element": upper_element,
            "upper_stage": long_life(upper_element, branch),
            "lower_star": lower_star,
            "lower_element": element_for_star(element, lower_star),
            "lower_stage": long_life(element, branch),
        })
    return {"mountain_element": element, "pillars": rows}
