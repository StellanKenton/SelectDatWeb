from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

from capture_reference import BrowserSession, BASE_URL, login, redact


OUT = Path("reference_details")
OUT.mkdir(parents=True, exist_ok=True)


def capture(browser: BrowserSession, path: str, stem: str, referer: str) -> dict:
    response = browser.request("GET", path, headers={"Referer": referer})
    html = redact(response.text)
    (OUT / f"{stem}.html").write_text(html, encoding="utf-8")
    # Keep a plain-text-ish copy useful for quick inspection without a browser.
    text = " ".join(html.replace("\r", " ").replace("\n", " ").split())
    (OUT / f"{stem}.txt").write_text(text, encoding="utf-8")
    return {
        "stem": stem,
        "status": response.status_code,
        "url": response.url.split("?")[0],
        "bytes": len(response.content),
        "contains_login_prompt": "使用前请先点击顶部【登录】" in response.text or "请先登录" in response.text,
    }


def main() -> int:
    browser = BrowserSession()
    logged, state = login(browser)

    allshi_qs = urlencode(
        {
            "Action": "allshichen",
            "shoucangid": "",
            "rulueri": "2461292",
            "zuobagua": "",
            "ershisishan": "",
            "jian": "",
            "fenjin": "",
            "xiufang": "",
            "dagua": "",
            "daguaval": "",
            "nianming": "",
            "wangming": "",
            "yongshi": "0",
            "yiji": "all",
        }
    )
    wuxing_qs = urlencode(
        {
            "Action": "wuxing",
            "bianhao": "2026090800",
            "bazi": "丙;丁;乙;丙;午;酉;酉;子",
            "ershisishan": "1",
        }
    )

    report = {
        "login_state": state.get("shenhe"),
        "pages": [
            capture(
                browser,
                f"/zeridashi/yixue/zeri.php?{allshi_qs}",
                "allshichen_20260908",
                logged.url,
            ),
            capture(
                browser,
                f"/zeridashi/yixue/zeri_jiexi.php?{wuxing_qs}",
                "wuxing_2026090800",
                logged.url,
            ),
        ],
    }
    (OUT / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
