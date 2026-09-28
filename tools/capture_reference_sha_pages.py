from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from capture_reference import BrowserSession, login, redact


OUT = Path("reference_sha_pages")
OUT.mkdir(parents=True, exist_ok=True)

BASE_DATE = date(2026, 9, 8)
BASE_RULUERI = 2461292

TARGETS = [
    "2026-09-08",
    "2026-09-11", "2026-09-12", "2026-09-14",
    "2026-09-16",
    "2026-09-19", "2026-09-20", "2026-09-22", "2026-09-24",
    "2026-09-26", "2026-09-27", "2026-09-30",
    "2026-10-01", "2026-10-02", "2026-10-04", "2026-10-05",
    "2026-10-06", "2026-10-08",
]


def rulueri_for(iso: str) -> int:
    d = date.fromisoformat(iso)
    return BASE_RULUERI + (d - BASE_DATE).days


def main() -> int:
    browser = BrowserSession()
    logged, state = login(browser)
    report = {"login_state": state.get("shenhe"), "pages": []}

    for iso in TARGETS:
        qs = urlencode(
            {
                "Action": "allshichen",
                "shoucangid": "",
                "rulueri": str(rulueri_for(iso)),
                "zuobagua": "1",
                "ershisishan": "1",
                "jian": "亥巳",
                "fenjin": "乙亥",
                "xiufang": "",
                "dagua": "风地观",
                "daguaval": "2;2",
                "nianming": "",
                "wangming": "",
                "yongshi": "0",
                "yiji": "all",
            }
        )
        response = browser.request(
            "GET",
            f"/zeridashi/yixue/zeri.php?{qs}",
            headers={"Referer": logged.url},
        )
        html = redact(response.text)
        stem = iso.replace("-", "")
        (OUT / f"{stem}.html").write_text(html, encoding="utf-8")
        report["pages"].append(
            {
                "date": iso,
                "rulueri": rulueri_for(iso),
                "status": response.status_code,
                "bytes": len(response.content),
                "has_12_lessons": "显示：12个日课" in response.text,
            }
        )

    (OUT / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
