from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from browser_reference_sample import BASE, login, wait_frame, select_value, redact


OUT = Path("reference_level_scan")
OUT.mkdir(parents=True, exist_ok=True)


def result_page(driver) -> tuple[int, str, str]:
    wait_frame(driver, "centerFrame")
    WebDriverWait(driver, 45).until(
        lambda d: "显示：" in d.page_source and "个日课" in d.page_source
    )
    text = driver.find_element(By.TAG_NAME, "body").text
    html = driver.page_source
    m = re.search(r"显示：\s*(\d+)个日课", text)
    return (int(m.group(1)) if m else -1), html, text


def parse_wuxing_rows(html: str) -> list[dict]:
    pattern = re.compile(
        r'id="(?P<id>\d+)" class="li_sizhu_top">(?P<mountain>[^<]+)</div>\s*'
        r'<div class="li_geju"[^>]*JieXi\([^)]*?\'wuxing\',\'(?P<bazi>[^\']+)\'[^)]*\)'
        r'[^>]*>.*?<a[^>]*>(?P<geju>[^<]+)</a>',
        re.S,
    )
    return [m.groupdict() for m in pattern.finditer(html)]


def capture_explanation(driver, sample: dict, name: str) -> None:
    original = driver.current_window_handle
    query = urlencode({
        "Action": "wuxing",
        "bianhao": sample["id"],
        "bazi": sample["bazi"],
        "ershisishan": "1",
    })
    driver.execute_script(
        "window.open(arguments[0], '_blank');",
        f"{BASE}/zeridashi/yixue/zeri_jiexi.php?{query}",
    )
    WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) >= 2)
    popup = [h for h in driver.window_handles if h != original][-1]
    driver.switch_to.window(popup)
    WebDriverWait(driver, 20).until(lambda d: len(d.page_source) > 300)
    (OUT / f"explain_{name}.html").write_text(
        redact(driver.page_source), encoding="utf-8"
    )
    (OUT / f"explain_{name}.txt").write_text(
        redact(driver.find_element(By.TAG_NAME, "body").text), encoding="utf-8"
    )
    driver.close()
    driver.switch_to.window(original)


def main() -> int:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1820,800")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        login(driver)

        wait_frame(driver, "top1Frame")
        select_value(driver, "rilitype", "干支")
        select_value(driver, "ganzhinian", "163")
        select_value(driver, "ganzhiri", "全部")
        month_el = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ganzhiyue"))
        )
        month_options = [
            {"value": o.get_attribute("value"), "label": o.text.strip()}
            for o in Select(month_el).options
            if o.get_attribute("value")
        ]

        wait_frame(driver, "shuruFrame")
        select_value(driver, "yiji", "all")
        select_value(driver, "yongshi", "0")
        select_value(driver, "zuobagua", "1")
        time.sleep(0.4)
        select_value(driver, "ershisishan", "1")
        time.sleep(0.4)
        select_value(driver, "jian", "亥巳")
        select_value(driver, "fenjin", "乙亥")
        select_value(driver, "dagua", "2;2")

        report = []
        explain_samples: dict[str, dict] = {}
        for month in month_options:
            wait_frame(driver, "top1Frame")
            select_value(driver, "ganzhiyue", month["value"])
            time.sleep(0.5)

            row = {"month": month["label"], "value": month["value"]}
            for level in ("大吉", "小吉"):
                wait_frame(driver, "shuruFrame")
                select_value(driver, "paichubiaozhi", level)
                driver.execute_script("toframes();")
                count, page_html_raw, body_text_raw = result_page(driver)
                row[level] = count
                if count > 0:
                    safe_level = {"大吉": "daji", "小吉": "xiaoji"}[level]
                    safe_month = re.sub(r"[^0-9A-Za-z_-]+", "_", month["value"])
                    body_text = redact(body_text_raw)
                    page_html = redact(page_html_raw)
                    (OUT / f"{safe_month}_{safe_level}.txt").write_text(body_text, encoding="utf-8")
                    (OUT / f"{safe_month}_{safe_level}.html").write_text(page_html, encoding="utf-8")
                    parsed = parse_wuxing_rows(page_html_raw)
                    row[level + "_rows"] = parsed
                    for item in parsed:
                        geju = item["geju"].lstrip(".")
                        explain_samples.setdefault(geju, item)
                time.sleep(1.0)
            report.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)

        (OUT / "month_counts.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        nonzero = [r for r in report if r["大吉"] > 0 or r["小吉"] > 0]
        print("NONZERO=" + json.dumps(nonzero, ensure_ascii=False))
        (OUT / "explain_samples.json").write_text(
            json.dumps(explain_samples, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for geju, sample in explain_samples.items():
            safe = re.sub(r"[^0-9A-Za-z_-]+", "_", geju).strip("_") or "sample"
            capture_explanation(driver, sample, safe)
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
