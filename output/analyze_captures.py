"""Analyze saved visible-site captures without making any website requests."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import traceback
from pathlib import Path


OUTPUT = Path(__file__).resolve().parent
ROOT = OUTPUT.parent
SEARCH_ACTIONS = {
    "B01": "顶部评课搜索（前次会话已显示的结果）",
    "B02": "顶部评课搜索",
    "B03": "顶部评课搜索",
    "B04": "顶部评课搜索",
    "B05": "顶部评课搜索",
    "B06": "右侧择课搜索",
}
sys.path.insert(0, str(ROOT))

from core.shanjia import calculate_days  # noqa: E402


def read_case(case_id: str) -> dict:
    name = f"{case_id}_stale_capture.json" if case_id == "B05" else f"{case_id}_reference.json"
    case = json.loads((OUTPUT / name).read_text(encoding="utf-8"))
    if "fields" not in case:
        case["fields"] = case["top"] | case["right"]
    return case


def selected(case: dict, field: str) -> str:
    return str(case["fields"][field]["value"])


def reference_cards(text: str) -> list[str]:
    chunks = text.split("[打印] ")
    return [("[打印] " + re.split(r"\n显示：\d+个日课。", chunk, maxsplit=1)[0]).rstrip("\n")
            for chunk in chunks[1:]]


def run_existing_tests() -> dict:
    path = ROOT / "tests" / "test_shanjia.py"
    spec = importlib.util.spec_from_file_location("existing_test_shanjia", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    passed, failed = [], []
    for name in sorted(vars(module)):
        fn = getattr(module, name)
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                passed.append(name)
            except Exception:
                failed.append({"name": name, "traceback": traceback.format_exc()})
    return {"runner": "direct function invocation; pytest unavailable in project venv", "passed": passed, "failed": failed}


def analyze_case(case_id: str) -> dict:
    case = read_case(case_id)
    fields = case["fields"]
    year, month = int(selected(case, "gonglinian")), int(selected(case, "gongliyue"))
    day = selected(case, "gongliri")
    from calendar import monthrange

    start = f"{year:04d}-{month:02d}-{1 if day == '全部' else int(day):02d}"
    end_day = monthrange(year, month)[1] if day == "全部" else int(day)
    end = f"{year:04d}-{month:02d}-{end_day:02d}"
    hours = [int(x["value"]) for x in case.get("selected_times", case.get("selected_top_inputs", []))]
    level = {"1级大吉": "大吉", "2级小吉": "小吉", "3级日干生旺": "生旺", "4级日干次旺": "耗"}.get(fields["paichubiaozhi"]["text"], "全部")
    payload = {
        "start_date": start,
        "end_date": end,
        "hours": hours,
        "use_type": fields["yongshi"]["text"],
        "mountain_id": int(selected(case, "ershisishan")),
        "level": level,
        "edition": {"all": "协纪版", "all1": "潮汕版", "all2": "协纪+潮汕", "off": "不显示"}.get(selected(case, "yiji"), "协纪版"),
    }
    local = calculate_days(payload)
    cards = reference_cards(case["center_text"])
    dates = [m.group(1) for card in cards if (m := re.search(r"公历:(\d+月\d+日)", card))]
    observed_hours = sorted({int(value) for value in re.findall(r"(?m)^(\d+)点$", case["center_text"])})
    hour_echo_matches = observed_hours == sorted(hours)
    ref_count = case.get("result_count", int(re.search(r"显示：(\d+)个日课", case["center_text"]).group(1)))
    return {
        "case_id": case_id,
        "captured_at": case["captured_at"],
        "search_action": SEARCH_ACTIONS[case_id],
        "effective_site_input": {
            "date": [start, end], "hours": hours,
            "use_type": fields["yongshi"]["text"],
            "mountain": fields["ershisishan"]["text"],
            "level": fields["paichubiaozhi"]["text"],
            "edition": fields["yiji"]["text"],
            "jian": fields["jian"]["text"],
            "fenjin": fields["fenjin"]["text"],
            "dagua": fields["dagua"]["text"],
        },
        "reference_count": ref_count,
        "reference_visible_card_count": len(cards),
        "reference_first_date": dates[0] if dates else None,
        "reference_last_date": dates[-1] if dates else None,
        "reference_card_hours": observed_hours,
        "hour_echo_matches_selected": hour_echo_matches,
        "capture_valid": hour_echo_matches,
        "local_payload": payload,
        "local_count": local["count"],
        "local_first_lesson": local["results"][0]["lesson_id"] if local["results"] else None,
        "count_equal": ref_count == local["count"] if hour_echo_matches else None,
        "local_comparison_scope": (
            "diagnostic_only_top_search_may_ignore_right_filters" if case_id != "B06"
            else "partial_right_search_jian_fenjin_dagua_not_calculated_locally"
        ),
        "reference_full_text_equal": None,
        "reference_full_text_equal_reason": "本地界面未生成原站完整日课字段，无法逐字比较",
    }


def main() -> None:
    ids = ["B01", "B02", "B03", "B04", "B05", "B06"]
    cases = [analyze_case(case_id) for case_id in ids]
    captures = {case_id: read_case(case_id) for case_id in ids}
    b02 = reference_cards(captures["B02"]["center_text"])
    b03 = reference_cards(captures["B03"]["center_text"])
    sep28 = [card for card in b02 if "公历:9月28日" in card]
    cross_check = {
        "B02_contains_September_28_card": len(sep28) == 1,
        "B02_September_28_vs_B03_full_card_equal": len(sep28) == len(b03) == 1 and sep28[0] == b03[0],
    }
    word_cross_check = {
        "source": "C:/Users/senki/Desktop/Destiny/Word/十天干日配六十甲子时_可搜索文字版.docx，第1页，乙日行",
        "rule": {"乙日子时": "丙子", "乙日午时": "壬午"},
        "site_B03_pillars": "丙午 丁酉 乙巳 丙子",
        "site_B04_pillars": "丙午 丁酉 乙巳 壬午",
        "agrees_on_tested_hours": True,
    }
    result = {
        "scope": "Six saved UI captures; no network access in this analyzer",
        "existing_tests": run_existing_tests(),
        "cases": cases,
        "reference_cross_check": cross_check,
        "word_cross_check": word_cross_check,
        "limitations": [
            "B01 was captured from the already visible query result; no new submission was made for it this turn.",
            "B05 has a stale result: the hour selector says 22 but the card says 12; exclude it from comparisons.",
            "B01-B05 used the top evaluation search, while B06 used the right lesson search. These actions may have different filtering semantics; do not infer an algorithm mismatch from the count differences alone.",
            "B06 changed use type and the site also reset jian, fenjin and dagua; it is not a single-variable differential test.",
            "The local calculation omits some website default sha filters, so count differences are diagnostic, not isolated causal proof.",
            "No claim of complete-text parity or 95 percent population parity is supported.",
        ],
    }
    (OUTPUT / "comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 原站实测与本地对照（第一轮）", "",
        "原站数据经用户现有 Edge 标签页的可见界面读取；有效结果保存在对应的 `Bxx_reference.json`，B05 旧画面保存在 `B05_stale_capture.json`。本脚本不访问网站。", "",
        "| 用例 | 原站查询按钮 | 原站日课 | 本地日课 | 结果状态 |", "| --- | --- | ---: | ---: | --- |",
    ]
    for case in cases:
        status = "抓取无效：时辰回显不符" if not case["capture_valid"] else ("数值相同，未证明等价" if case["count_equal"] else "数值不同，条件未完全等价")
        action = "顶部评课搜索" if case["case_id"] != "B06" else "右侧择课搜索"
        lines.append(f"| {case['case_id']} | {action} | {case['reference_count']} | {case['local_count']} | {status} |")
    lines += [
        "", f"原有测试：{len(result['existing_tests']['passed'])} 通过，{len(result['existing_tests']['failed'])} 失败；项目虚拟环境没有安装 pytest，故直接调用现有 `test_` 函数。",
        "", f"B02 月结果含 9 月 28 日卡片：{'是' if cross_check['B02_contains_September_28_card'] else '否'}；与 B03 单日卡片逐字相同：{'是' if cross_check['B02_September_28_vs_B03_full_card_equal'] else '否'}。",
        "", "## 与 Word 文档核对", "",
        "`十天干日配六十甲子时_可搜索文字版.docx` 第 1 页的乙日行写明：子时为丙子，午时为壬午。原站 B03 的四柱显示为丙午／丁酉／乙巳／丙子，B04 为丙午／丁酉／乙巳／壬午。这两个实测时柱与文档相符；其他日干和时辰仍未实测。",
        "", "## 解释边界", "",
        "- 当前本地界面只渲染日期、四柱、评分、简短吉凶和时辰，原站卡片还含通书宜忌、神煞、斗首、飞星等内容；整份日课逐字一致尚不能验证。",
        "- B05 的顶部时辰已选 22 点，结果卡仍显示 12 点，是页面尚未刷新完成时的旧结果；这条不参与实测结论。",
        "- B01–B05 使用顶部“评课搜索”，B06 使用右侧“择课搜索”。前者在单月返回每天一张、单日返回一张，可能与右侧等级筛选的语义不同；这些数量差异尚不能单独证明本地算法错误。",
        "- B06 选择“开业”后，原站自动改变兼山、分金和大卦；记录中的生效条件以页面回显为准，不能把差异单独归因于用事。",
        "- 本地程序尚未覆盖原站所有默认神煞过滤；即使数量偶然相同，也不代表计算或全文一致。",
        "- 本轮只核对所选样本；不能据此声称 95% 的整体一致率。",
        "", "## 后续网站查询", "",
        "按 `design/exact_parity_test_plan.md` 的低频限制，本轮已停止继续查询。本轮 B02–B06 共提交 5 条计划案例，另有一次因年份切换使月份重置而提交的 2026 年 12 月查询。下轮应先用右侧“择课搜索”重做一个小范围基线，并在结果窗格回显日期和时辰后才采集，再继续后续案例。",
    ]
    (OUTPUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"cases": [{"id": x["case_id"], "reference": x["reference_count"], "local": x["local_count"], "valid": x["capture_valid"], "hour_echo": x["reference_card_hours"]} for x in cases], "tests_passed": len(result["existing_tests"]["passed"]), "tests_failed": len(result["existing_tests"]["failed"]), "cross_check": cross_check}, ensure_ascii=False))


if __name__ == "__main__":
    main()
