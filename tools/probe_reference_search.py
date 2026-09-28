from __future__ import annotations

import json
from pathlib import Path

from capture_reference import BrowserSession, FormParser, login, redact


OUT = Path("reference_probe")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    browser = BrowserSession()
    logged, state = login(browser)

    initial = browser.request(
        "GET",
        "/zeridashi/yixue/zeri.php",
        headers={"Referer": logged.url},
    )
    parser = FormParser("form1")
    parser.feed(initial.text)
    payload = dict(parser.inputs)

    payload.update(
        {
            "Action": "kaishisousuo",
            "weizhi": "",
            "yongshiType": "",
            "yongshi": "0",
            "rilitype": "干支",
            "ganzhinian": "丙午",
            "ganzhiyue": "丁酉",
            "ganzhiri": "全部",
            "jieqinianxuhao": "163",
            "jieqiyuexuhao": "1952",
            "fanwei": "",
            "shichen": "0",
            "paichubiaozhi": "大吉",
            "zuobagua": "1",
            "ershisishan": "1",
            "jian": "亥巳",
            "fenjin": "乙亥",
            "dagua": "风地观",
            "daguaval": "2;2",
            "xiufang": "",
            "nianming": "",
            "wangming": "",
            "yueli": "",
            "rili": "",
            "mingshaguolv": "",
            "huamingshaguolv": "",
            "xiongsha": "",
            "jxiongsha": "",
            "yiji": "all",
            "zerifabiaozhi": "1",
        }
    )

    # form1 contains duplicate checkbox names in a real browser. For this first
    # parity sample only the currently selected method is needed.
    payload["Arry_zerifa[]"] = "六壬择日【时支】"

    result = browser.request(
        "POST",
        "/zeridashi/yixue/zeri.php",
        data=payload,
        headers={"Referer": initial.url},
    )

    text = redact(result.text)
    (OUT / "sample_build_ren.html").write_text(text, encoding="utf-8")
    (OUT / "payload.json").write_text(
        json.dumps({k: redact(str(v)) for k, v in payload.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "login_state": state.get("shenhe"),
        "status": result.status_code,
        "bytes": len(result.content),
        "contains_kaishisousuo": "kaishisousuo" in result.text,
        "contains_result_marker": "个日课" in result.text,
        "contains_20260928": "20260928" in result.text,
        "contains_login_prompt": "使用前请先点击顶部【登录】" in result.text,
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
