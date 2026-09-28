from __future__ import annotations

import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urljoin

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from browser_reference_sample import BASE, login, wait_frame, select_value


OUT = Path("reference_filter_isolation")
OUT.mkdir(parents=True, exist_ok=True)
INTERVAL = float(os.getenv("ZERIDASHI_REQUEST_INTERVAL", "1.5"))


def form_pairs(driver) -> list[tuple[str, str]]:
    wait_frame(driver, "centerFrame")
    return driver.execute_script(
        """
        const f = document.getElementById('form1');
        return Array.from(new FormData(f).entries()).map(([k,v]) => [k, String(v)]);
        """
    )


def replace_pair(pairs: list[tuple[str, str]], key: str, value: str) -> list[tuple[str, str]]:
    out = [(k, v) for k, v in pairs if k != key]
    out.append((key, value))
    return out


def session_from_driver(driver) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": driver.execute_script("return navigator.userAgent"),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
        "Referer": f"{BASE}/zeridashi/yixue/zeri.php",
    })
    for c in driver.get_cookies():
        s.cookies.set(c["name"], c["value"], domain=c.get("domain"), path=c.get("path", "/"))
    return s


def lesson_ids(html: str) -> list[str]:
    return sorted(set(re.findall(r'id="(\d{10})"\s+class="li_sizhu_top"', html)))


def post_variant(session: requests.Session, pairs: list[tuple[str, str]], filters: list[str]) -> dict:
    data = replace_pair(pairs, "xiongsha", ";".join(filters))
    data = replace_pair(data, "Action", "kaishisousuo")
    data = replace_pair(data, "paichubiaozhi", "全部")
    response = session.post(
        urljoin(BASE + "/", "zeridashi/yixue/zeri.php"),
        data=data,
        timeout=45,
        allow_redirects=True,
    )
    response.raise_for_status()
    ids = lesson_ids(response.text)
    m = re.search(r"显示：\s*(\d+)个日课", response.text)
    count = int(m.group(1)) if m else len(ids)
    time.sleep(INTERVAL)
    return {"count": count, "ids": ids}


def configure(driver) -> tuple[list[tuple[str, str]], list[str]]:
    wait_frame(driver, "top1Frame")
    select_value(driver, "rilitype", "干支")
    select_value(driver, "ganzhinian", "163")
    month = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "ganzhiyue"))
    )
    for option in Select(month).options:
        if "丁酉" in option.text:
            Select(month).select_by_visible_text(option.text)
            driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));", month
            )
            break
    select_value(driver, "ganzhiri", "全部")

    wait_frame(driver, "shuruFrame")
    select_value(driver, "yiji", "all")
    select_value(driver, "yongshi", "0")
    select_value(driver, "zuobagua", "1")
    time.sleep(0.35)
    select_value(driver, "ershisishan", "1")
    time.sleep(0.35)
    select_value(driver, "jian", "亥巳")
    select_value(driver, "fenjin", "乙亥")
    select_value(driver, "dagua", "2;2")
    select_value(driver, "paichubiaozhi", "全部")
    driver.execute_script("onloadok();")
    filters = driver.execute_script(
        "return (document.getElementById('xiongsha').value || '').split(';').filter(Boolean);"
    )
    pairs = form_pairs(driver)
    return pairs, filters


def main() -> int:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1820,800")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        login(driver)
        pairs, filters = configure(driver)
        session = session_from_driver(driver)

        baseline = post_variant(session, pairs, filters)
        report = {
            "filters": filters,
            "baseline_count": baseline["count"],
            "baseline_ids": baseline["ids"],
            "remove_one": {},
        }

        for name in filters:
            variant_filters = [x for x in filters if x != name]
            result = post_variant(session, pairs, variant_filters)
            added = sorted(set(result["ids"]) - set(baseline["ids"]))
            report["remove_one"][name] = {
                "count": result["count"],
                "delta": result["count"] - baseline["count"],
                "added_ids": added,
            }
            print(json.dumps({
                "filter": name,
                "count": result["count"],
                "delta": result["count"] - baseline["count"],
                "added_ids": added[:40],
            }, ensure_ascii=False), flush=True)

        (OUT / "isolation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("BASELINE=" + json.dumps({
            "count": baseline["count"],
            "filters": filters,
        }, ensure_ascii=False))
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
