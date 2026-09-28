from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

from capture_reference import BrowserSession, login, redact

OUT = Path("reference_explanations")
OUT.mkdir(parents=True, exist_ok=True)

RULES = [
    "月冲山", "日冲山", "时冲山",
    "月三杀", "日三杀", "时三杀",
    "月正阴府", "日正阴府", "时正阴府",
    "日正八煞", "时正八煞",
    "日星曜煞", "时星曜煞",
    "天星煞", "地曜煞", "日流太岁", "日消灭煞", "日山方煞",
]


def plain_text(html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def main() -> int:
    browser = BrowserSession()
    logged, state = login(browser)
    report = {"login_state": state.get("shenhe"), "rules": {}}
    for rule in RULES:
        qs = urlencode({
            "Action": "择日神煞",
            "zonglei": "择日神煞",
            "fenlei": "山家神煞",
            "type": "",
            "mingcheng": rule,
        })
        response = browser.request(
            "GET",
            f"/zeridashi/yixue/zeri_jiexi.php?{qs}",
            headers={"Referer": logged.url},
        )
        html = redact(response.text)
        text = redact(plain_text(html))
        safe = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]+", "_", rule).strip("_")
        (OUT / f"{safe}.html").write_text(html, encoding="utf-8")
        (OUT / f"{safe}.txt").write_text(text, encoding="utf-8")
        report["rules"][rule] = {
            "status": response.status_code,
            "bytes": len(response.content),
            "text": text[:4000],
        }
        time.sleep(0.5)
    (OUT / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for rule, info in report["rules"].items():
        print("###", rule)
        print(info["text"][:1200].replace("\n", " | "))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"capture explanations failed: {redact(str(exc))}", file=sys.stderr)
        raise
