from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from browser_reference_sample import BASE, login, redact


OUT = Path("reference_details")
OUT.mkdir(parents=True, exist_ok=True)


def capture(driver, url: str, stem: str) -> dict:
    driver.get(url)
    WebDriverWait(driver, 30).until(lambda d: len(d.page_source) > 300)
    html = redact(driver.page_source)
    text = redact(driver.find_element(By.TAG_NAME, "body").text)
    (OUT / f"{stem}.html").write_text(html, encoding="utf-8")
    (OUT / f"{stem}.txt").write_text(text, encoding="utf-8")
    return {
        "stem": stem,
        "url": url.split("?")[0],
        "html_bytes": len(html.encode("utf-8")),
        "text_chars": len(text),
        "contains_login_prompt": "使用前请先点击顶部【登录】" in text or "请先登录" in text,
    }


def main() -> int:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1000")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        login(driver)

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

        report = [
            capture(driver, f"{BASE}/zeridashi/yixue/zeri.php?{allshi_qs}", "allshichen_20260908"),
            capture(driver, f"{BASE}/zeridashi/yixue/zeri_jiexi.php?{wuxing_qs}", "wuxing_2026090800"),
        ]
        (OUT / "summary.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False))
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
