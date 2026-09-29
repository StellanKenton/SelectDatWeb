"""Generate the small, adaptive 山家择日 reference test set.

Run from the repository root:
    python design/generate_exact_parity_cases.py

The file contains inputs and hypotheses, not captured reference answers.
The 12 review cases must remain unread until the rules are frozen.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES_PATH = HERE / "exact_parity_cases.jsonl"
MANIFEST_PATH = HERE / "exact_parity_case_manifest.json"


def query(
    start: str,
    end: str | None = None,
    *,
    use: str = "建造",
    mountain: int | None = 1,
    hour: int = 0,
    level: str = "全部",
    edition: str = "协纪版",
    **extra: object,
) -> dict:
    result = {
        "calendar_type": "公历",
        "start_date": start,
        "end_date": end or start,
        "hours": [hour],
        "use_type": use,
        "mountain_id": mountain,
        "level": level,
        "edition": edition,
        "sha_filters": "site_default",
        "life_years": [],
        "deceased_years": [],
    }
    result.update(extra)
    return result


cases: list[dict] = []


def add(
    case_id: str,
    phase: str,
    value: dict,
    question: str,
    source: str,
    *,
    base_case: str | None = None,
    run_if: str | None = None,
    observed_count: int | None = None,
) -> None:
    item = {
        "id": case_id,
        "phase": phase,
        "input": value,
        "question": question,
        "word_source": source,
        "oracle": "full_reference_text_not_yet_captured",
        "compare": ["result_count", "ordered_full_lesson_text"],
    }
    if base_case:
        item["base_case"] = base_case
    if run_if:
        item["run_if"] = run_if
    if observed_count is not None:
        item["previously_observed_count_only"] = observed_count
    cases.append(item)


add("B01", "baseline", query("2011-09-01", "2011-09-30", level="1级大吉"),
    "复现原始月范围并收集多张完整日课", "择日教材；知识重点", observed_count=30)
add("B02", "baseline", query("2026-09-01", "2026-09-30", level="1级大吉"),
    "用一个普通月份建立建造与壬山基线", "择日教材；二十四山造葬凶煞表")
add("B03", "baseline", query("2026-09-28", level="1级大吉"),
    "月查询与单日查询的同日卡片是否逐字相同", "十天干日配六十甲子时", observed_count=1)
add("B04", "baseline", query("2026-09-28", hour=12, level="1级大吉"),
    "只改午时后的时柱与时煞变化", "十天干日配六十甲子时", base_case="B03")
add("B05", "baseline", query("2026-09-28", hour=22, level="1级大吉"),
    "亥时与子时的日课差异", "十天干日配六十甲子时", base_case="B03")
add("B06", "baseline", query("2026-09-01", "2026-09-30", use="开业", level="1级大吉"),
    "同月同山切换用事后的入选日和全文", "择日教材", base_case="B02", observed_count=1)
add("B07", "baseline", query("2026-09-01", "2026-09-30", use="开业", mountain=13, level="1级大吉"),
    "只改坐山为丙山的过滤效果", "二十四山造葬凶煞表", base_case="B06", observed_count=0)
add("B08", "baseline", query("2026-09-01", "2026-09-30", use="安葬"),
    "安葬规则与建造规则差异", "择日教材；二十四山造葬凶煞表", base_case="B02")
add("B09", "baseline", query("2026-09-01", "2026-09-30", use="修方"),
    "修方使用山家与方位条件的方式", "择日教材", base_case="B02")
add("B10", "baseline", query("2026-09-22"),
    "秋分前一天的节气和月柱", "1五行择日基础教材")
add("B11", "baseline", query("2026-09-23"),
    "秋分当天的节气和月柱", "1五行择日基础教材", base_case="B10")
add("B12", "baseline", query("2024-02-29"),
    "公历闰日的历法和四柱", "1五行择日基础教材")
add("B13", "baseline", query("2023-03-22"),
    "农历闰月候选边界的显示", "1五行择日基础教材")
add("B14", "baseline", query("2026-09-28", level="1级大吉", edition="潮汕版"),
    "只改宜忌版本时全文如何变化", "择日教材", base_case="B03")
add("B15", "baseline", query("2026-09-28"),
    "只放宽五行等级的候选与文字变化", "知识重点", base_case="B03")
add("B16", "baseline", query("2026-09-28", life_years=[1984]),
    "增加甲子年命后的冲命与命煞文字", "六十年命凶煞表(1)", base_case="B15")


# Conditional probes are a budget, not a mandatory queue. Execute a case only
# when its run_if condition is met by document comparison or a prior mismatch.
adaptive = [
    ("A01", "B02", {"mountain_id": 7}, "木山甲与水山壬的五行／山煞分歧", "知识重点；二十四山造葬凶煞表"),
    ("A02", "B02", {"mountain_id": 5}, "土山艮与水山壬的分歧", "知识重点；二十四山造葬凶煞表"),
    ("A03", "B02", {"mountain_id": 19}, "金山庚与水山壬的分歧", "知识重点；二十四山造葬凶煞表"),
    ("A04", "B02", {"mountain_id": 13}, "火山丙与水山壬的分歧", "知识重点；二十四山造葬凶煞表"),
    ("A05", "B03", {"hours": [2]}, "子、丑相邻时辰的换柱差异", "十天干日配六十甲子时"),
    ("A06", "B03", {"jian": "子午"}, "兼左与兼右的冲兼山差异", "二十四山造葬凶煞表"),
    ("A07", "B03", {"fenjin": "丁亥"}, "分金是否进入计算或只改变展示", "1五行择日基础教材"),
    ("A08", "B03", {"dagua": "水地比"}, "大卦是否进入计算或只改变展示", "1五行择日基础教材"),
    ("A09", "B03", {"sha_filters": {"invert_default": "日冲山"}}, "日冲山开关的作用与优先级", "二十四山造葬凶煞表"),
    ("A10", "B03", {"sha_filters": {"invert_default": "日三杀"}}, "日三杀开关的作用与优先级", "二十四山造葬凶煞表"),
    ("A11", "B08", {"deceased_years": [1960]}, "安葬亡命输入是否改变入选和文字", "六十年命凶煞表(1)"),
    ("A12", "B03", {"level": "2级小吉"}, "等级边界是否只过滤或还改写卡片", "知识重点"),
]
index = {item["id"]: item for item in cases}
for case_id, base_id, delta, question, source in adaptive:
    value = dict(index[base_id]["input"])
    value.update(delta)
    add(case_id, "adaptive", value, question, source, base_case=base_id,
        run_if="仅当文档规则仍有歧义，或基线全文与本地预测不一致时执行")


# Keep these cases unopened until the inferred implementation is frozen.
review = [
    ("2010-01-15", "建造", 1, 0),
    ("2015-06-21", "建造", 7, 12),
    ("2019-12-22", "安葬", 19, 18),
    ("2021-02-03", "开业", 13, 0),
    ("2024-02-29", "入宅", 5, 12),
    ("2026-06-21", "修方", 11, 18),
    ("2027-09-23", "建造", 15, 0),
    ("2030-03-20", "安门", 24, 12),
    ("2035-07-07", "作灶", 8, 0),
    ("2040-11-07", "交易", None, 0),
    ("2000-12-31", "造坟", 17, 12),
    ("2049-09-23", "建造", 2, 18),
]
for number, (day, use, mountain, hour) in enumerate(review, 1):
    add(f"R{number:02d}", "review_holdout",
        query(day, use=use, mountain=mountain, hour=hour),
        "锁定规则后对未见过的日期与用事做整卡逐字检验",
        "综合文档")


with CASES_PATH.open("w", encoding="utf-8", newline="\n") as handle:
    for case in cases:
        handle.write(json.dumps(case, ensure_ascii=False, separators=(",", ":")) + "\n")

data = CASES_PATH.read_bytes()
MANIFEST_PATH.write_text(json.dumps({
    "schema_version": 2,
    "case_count": len(cases),
    "phase_counts": dict(Counter(case["phase"] for case in cases)),
    "minimum_site_queries": 28,
    "maximum_planned_site_queries": 40,
    "adaptive_cases_are_optional": True,
    "full_reference_text_captured": False,
    "jsonl_sha256": hashlib.sha256(data).hexdigest(),
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"Generated {len(cases)} cases in {CASES_PATH}")
