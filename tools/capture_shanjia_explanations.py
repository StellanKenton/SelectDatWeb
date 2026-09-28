from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlencode

from capture_reference import BrowserSession, login, redact

OUT = Path("reference_explanations")
OUT.mkdir(parents=True, exist_ok=True)

NAMES = [
    "冲山", "三杀", "正阴府", "正八煞", "星曜煞", "天星煞", "地曜煞",
    "日流太岁", "消灭煞", "山方煞",
]


def html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def main() -> int:
    browser = BrowserSession()
    logged, _ = login(browser)
    summary = {}
    for name in NAMES:
        query = urlencode(
            {
                "Action": "择日神煞",
                "zonglei": "择日神煞",
                "fenlei": "山家神煞",
                "type": "",
                "mingcheng": name,
            }
        )
        response = browser.request(
            "GET",
            f"/zeridashi/yixue/zeri_jiexi.php?{query}",
            headers={"Referer": logged.url},
        )
        html = redact(response.text)
        text = redact(html_to_text(response.text))
        (OUT / f"{name}.html").write_text(html, encoding="utf-8")
        (OUT / f"{name}.txt").write_text(text, encoding="utf-8")
        summary[name] = {
            "status": response.status_code,
            "chars": len(text),
            "login_prompt": "请先登录" in text,
        }
        print(f"{name}: {len(text)} chars", flush=True)

    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
