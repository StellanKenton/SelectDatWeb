from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from browser_reference_sample import login, wait_frame, select_value, redact


OUT = Path("reference_level_scan")
OUT.mkdir(parents=True, exist_ok=True)


def result_count(driver) -> int:
    wait_frame(driver, "centerFrame")
    WebDriverWait(driver, 45).until(
        lambda d: "显示：" in d.page_source and "个日课" in d.page_source
    )
    text = driver.find_element(By.TAG_NAME, "body").text
    m = re.search(r"显示：\s*(\d+)个日课", text)
    return int(m.group(1)) if m else -1


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
        for month in month_options:
            wait_frame(driver, "top1Frame")
            select_value(driver, "ganzhiyue", month["value"])
            time.sleep(0.5)

            row = {"month": month["label"], "value": month["value"]}
            for level in ("大吉", "小吉"):
                wait_frame(driver, "shuruFrame")
                select_value(driver, "paichubiaozhi", level)
                driver.execute_script("toframes();")
                row[level] = result_count(driver)
                if row[level] > 0:
                    safe_level = {"大吉": "daji", "小吉": "xiaoji"}[level]
                    safe_month = re.sub(r"[^0-9A-Za-z_-]+", "_", month["value"])
                    body_text = redact(driver.find_element(By.TAG_NAME, "body").text)
                    page_html = redact(driver.page_source)
                    (OUT / f"{safe_month}_{safe_level}.txt").write_text(body_text, encoding="utf-8")
                    (OUT / f"{safe_month}_{safe_level}.html").write_text(page_html, encoding="utf-8")
                time.sleep(1.0)
            report.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)

        (OUT / "month_counts.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        nonzero = [r for r in report if r["大吉"] > 0 or r["小吉"] > 0]
        print("NONZERO=" + json.dumps(nonzero, ensure_ascii=False))
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
