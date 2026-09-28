from __future__ import annotations

import json
import re
import time
from html import unescape
from pathlib import Path

from capture_reference import BrowserSession, login, redact

OUT = Path("reference_request_isolation")
OUT.mkdir(parents=True, exist_ok=True)
PAUSE = 2.0

BASE_PAYLOAD = {
    "formid": "择日",
    "Action": "kaishisousuo",
    "weizhi": "",
    "bianhao": "2026092816",
    "shoucangid": "",
    "yongshiType": "",
    "yongshi": "0",
    "shichenbiaozhi": "",
    "xuanzhong": "",
    "rilitype": "干支",
    "nonglinian": "2026",
    "nongliyue": "八",
    "nongliri": "全部",
    "gonglinian": "2026",
    "gongliyue": "9",
    "gongliri": "全部",
    "shichen": "全部时辰",
    "ganzhinian": "丙午",
    "ganzhiyue": "丁酉",
    "ganzhiri": "全部",
    "fanwei": "范围",
    "paichubiaozhi": "全部",
    "xingsudaoshan": "",
    "sanhesanhui": "",
    "shanyueli": "",
    "shanwuxing": "",
    "yueli": "",
    "rili": "",
    "jieqinianxuhao": "163",
    "jieqiyuexuhao": "1952",
    "rulueri": "",
    "zuobagua": "1",
    "ershisishan": "1",
    "jian": "亥巳",
    "fenjin": "乙亥",
    "xiufang": "",
    "dagua": "风地观",
    "daguaval": "2;2",
    "shenshawei1": "1",
    "shenshawei2": "",
    "nianming": "",
    "wangming": "",
    "mingshaguolv": "命煞过滤",
    "huamingshaguolv": "命煞过滤",
    "guize": "",
    "weizhiid": "2026092816",
    "rijishi0": "竖造",
    "rijishi1": "",
    "rijishi2": "",
    "rijishi3": "",
    "xiongsha": "月冲山;日冲山;时冲山;月三杀;日三杀;时三杀;月正阴府;日正阴府;时正阴府;日正八煞;时正八煞;日星曜煞;时星曜煞;天星煞;地曜煞;日流太岁;日消灭煞;日山方煞",
    "jxiongsha": "",
    "key": "",
    "keyval": "",
    "yiji": "all",
    "yincang1": "",
    "yincang2": "",
    "yincang3": "",
    "shike": "",
    "shoucangok": "",
    "paixu": "山煞",
    "zerifabiaozhi": "1",
}

DEFAULT_SHA = [x for x in BASE_PAYLOAD["xiongsha"].split(";") if x]
DEFAULT_DAY_JI = ["竖造"]


def html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def parse_result(text: str) -> dict:
    count_m = re.search(r"显示：\s*(\d+)个日课", text)
    pairs = []
    for block in text.split("[打印]")[1:]:
        dm = re.search(r"公历:(\d+)月(\d+)日", block)
        hm = re.search(r"\n\s*(\d{1,2})点\s*\n\s*时[吉凶]", block)
        if dm and hm:
            pairs.append(
                f"2026-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}T{int(hm.group(1)):02d}"
            )
    return {
        "count": int(count_m.group(1)) if count_m else -1,
        "pair_count": len(pairs),
        "pairs": pairs,
        "dates": sorted({p[:10] for p in pairs}),
    }


def run_variant(
    browser: BrowserSession,
    name: str,
    sha_values: list[str],
    day_ji: list[str],
) -> dict:
    payload = dict(BASE_PAYLOAD)
    payload["xiongsha"] = ";".join(sha_values)
    payload["rijishi0"] = day_ji[0] if len(day_ji) > 0 else ""
    payload["rijishi1"] = day_ji[1] if len(day_ji) > 1 else ""
    payload["rijishi2"] = day_ji[2] if len(day_ji) > 2 else ""
    payload["rijishi3"] = day_ji[3] if len(day_ji) > 3 else ""

    response = browser.request(
        "POST",
        "/zeridashi/yixue/zeri.php",
        data=payload,
        headers={"Referer": f"{browser.session.headers.get('Referer','') or 'http://zeridashi.top/zeridashi/yixue/zeri.php'}"},
    )
    safe_html = redact(response.text)
    text = redact(html_to_text(response.text))
    (OUT / f"{name}.html").write_text(safe_html, encoding="utf-8")
    (OUT / f"{name}.txt").write_text(text, encoding="utf-8")
    result = parse_result(text)
    result["login_prompt"] = "使用前请先点击顶部【登录】" in text
    result["bytes"] = len(response.content)
    time.sleep(PAUSE)
    return result


def main() -> int:
    browser = BrowserSession()
    logged, state = login(browser)

    # Refresh center page once inside the authenticated session before replay.
    browser.request(
        "GET",
        "/zeridashi/yixue/zeri.php",
        headers={"Referer": logged.url},
    )

    baseline = run_variant(browser, "baseline", DEFAULT_SHA, DEFAULT_DAY_JI)
    if baseline["count"] != 78:
        raise RuntimeError(
            f"真实表单复放基线应为78，实际={baseline['count']} "
            f"login={state.get('shenhe')} prompt={baseline['login_prompt']}"
        )

    none = run_variant(browser, "none", [], [])
    day_ji_only = run_variant(browser, "day_ji_only", [], DEFAULT_DAY_JI)
    all_sha_only = run_variant(browser, "all_sha_only", DEFAULT_SHA, [])

    none_pairs = set(none["pairs"])
    individual = {}
    for i, rule in enumerate(DEFAULT_SHA):
        item = run_variant(browser, f"sha_{i:02d}", [rule], [])
        excluded = sorted(none_pairs - set(item["pairs"]))
        item["excluded_pairs"] = excluded
        item["excluded_dates"] = sorted({x[:10] for x in excluded})
        individual[rule] = item
        print(
            f"{i+1:02d}/{len(DEFAULT_SHA)} {rule}: "
            f"count={item['count']} excluded={len(excluded)}",
            flush=True,
        )

    result = {
        "login_state": state.get("shenhe"),
        "baseline": baseline,
        "none": none,
        "day_ji_only": day_ji_only,
        "all_sha_only": all_sha_only,
        "default_sha": DEFAULT_SHA,
        "default_day_ji": DEFAULT_DAY_JI,
        "individual_sha": individual,
    }
    (OUT / "filter_isolation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "baseline": baseline["count"],
                "none": none["count"],
                "day_ji_only": day_ji_only["count"],
                "all_sha_only": all_sha_only["count"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
