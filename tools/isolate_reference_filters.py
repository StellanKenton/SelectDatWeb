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

BASE = os.getenv("ZERIDASHI_BASE_URL", "http://zeridashi.top").rstrip("/")
PHONE = os.environ["ZERIDASHI_PHONE"]
PASSWORD = os.environ["ZERIDASHI_PASSWORD"]
OUT = Path("reference_isolation")
OUT.mkdir(parents=True, exist_ok=True)


def redact(text: str) -> str:
    return text.replace(PHONE, "<PHONE>").replace(PASSWORD, "<PASSWORD>")


def wait_frame(driver, name: str, timeout: int = 30):
    driver.switch_to.default_content()
    WebDriverWait(driver, timeout).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, name))
    )


def select_value(driver, element_id: str, value: str):
    el = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    Select(el).select_by_value(value)
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", el
    )


def select_text_contains(driver, element_id: str, text: str):
    el = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    sel = Select(el)
    for option in sel.options:
        if text in option.text:
            sel.select_by_visible_text(option.text)
            driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", el
            )
            return
    raise RuntimeError(f"{element_id} 找不到 {text}")


def login(driver):
    driver.get(f"{BASE}/zeridashi/index-web/login.php?id={PHONE}")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "dianhua"))
    ).send_keys(PHONE)
    driver.find_element(By.ID, "pwd").send_keys(PASSWORD)
    driver.find_element(By.ID, "loginbutton").click()
    deadline = time.time() + 12
    while time.time() < deadline:
        for xp in [
            "//button[contains(normalize-space(.),'确定')]",
            "//a[contains(normalize-space(.),'确定')]",
            "//*[contains(@class,'aui_state_highlight')]",
        ]:
            for el in driver.find_elements(By.XPATH, xp):
                if el.is_displayed():
                    el.click()
                    WebDriverWait(driver, 30).until(
                        lambda d: len(d.find_elements(By.NAME, "top1Frame")) > 0
                    )
                    return
        time.sleep(0.2)
    raise RuntimeError("登录确认按钮未出现")


def configure_baseline(driver):
    wait_frame(driver, "top1Frame")
    select_value(driver, "rilitype", "干支")
    select_value(driver, "ganzhinian", "163")
    select_text_contains(driver, "ganzhiyue", "丁酉")
    select_value(driver, "ganzhiri", "全部")

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
    select_value(driver, "paichubiaozhi", "全部")
    time.sleep(0.5)
    driver.execute_script("toframes();")

    wait_frame(driver, "centerFrame")
    WebDriverWait(driver, 45).until(
        lambda d: "显示：" in d.page_source and "个日课" in d.page_source
    )
    time.sleep(0.8)


def parse_html(html: str) -> dict:
    count_m = re.search(r"显示：\s*(\d+)个日课", html)
    ids = sorted(set(re.findall(r'id=["\'](\d{10})["\']\s+class=["\']li_sizhu_top', html)))
    return {
        "count": int(count_m.group(1)) if count_m else -1,
        "lesson_ids": ids,
        "pair_count": len(ids),
    }


def fetch_variant(driver, sha_values: list[str], day_ji: list[str]) -> str:
    vals = list(day_ji[:4]) + [""] * (4 - len(day_ji[:4]))
    script = r"""
    const done = arguments[arguments.length - 1];
    const sha = arguments[0];
    const ji = arguments[1];
    const form = document.getElementById('form1');
    if (!form) { done({ok:false,error:'form1 missing'}); return; }
    const fd = new FormData(form);
    fd.set('Action', 'kaishisousuo');
    fd.set('paichubiaozhi', '全部');
    fd.set('xiongsha', sha.join(';'));
    for (let i=0;i<4;i++) fd.set('rijishi'+i, ji[i] || '');
    fetch(form.action || '/zeridashi/yixue/zeri.php', {
      method:'POST',
      body:fd,
      credentials:'same-origin',
      headers:{'X-Requested-With':'XMLHttpRequest'}
    }).then(async r => done({ok:r.ok,status:r.status,text:await r.text()}))
      .catch(e => done({ok:false,error:String(e)}));
    """
    result = driver.execute_async_script(script, sha_values, vals)
    if not result or not result.get("ok"):
        raise RuntimeError(f"variant POST failed: {result}")
    return str(result["text"])


def main() -> int:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1820,900")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_script_timeout(60)

    try:
        login(driver)
        configure_baseline(driver)
        baseline_html = redact(driver.page_source)
        baseline = parse_html(baseline_html)

        default_sha = driver.execute_script(
            "return (document.getElementById('xiongsha')?.value || '').split(';').filter(Boolean);"
        )
        default_ji = driver.execute_script(
            "return [0,1,2,3].map(i=>document.getElementById('rijishi'+i)?.value || '').filter(Boolean);"
        )

        variants = {}
        plan = [
            ("none", [], []),
            ("day_ji_only", [], default_ji),
            ("all_sha_only", default_sha, []),
            ("baseline", default_sha, default_ji),
        ]
        for name, sha, ji in plan:
            html = fetch_variant(driver, sha, ji)
            variants[name] = parse_html(html)
            time.sleep(1.4)

        none_ids = set(variants["none"]["lesson_ids"])
        individual = {}
        for rule in default_sha:
            html = fetch_variant(driver, [rule], [])
            parsed = parse_html(html)
            ids = set(parsed["lesson_ids"])
            parsed["excluded_ids"] = sorted(none_ids - ids)
            parsed["excluded_count"] = len(parsed["excluded_ids"])
            parsed["excluded_dates"] = sorted({x[:8] for x in parsed["excluded_ids"]})
            individual[rule] = parsed
            time.sleep(1.4)

        day_ji_ids = set(variants["day_ji_only"]["lesson_ids"])
        variants["day_ji_only"]["excluded_ids"] = sorted(none_ids - day_ji_ids)
        variants["day_ji_only"]["excluded_count"] = len(none_ids - day_ji_ids)

        report = {
            "baseline_page": baseline,
            "default_sha": default_sha,
            "default_day_ji": default_ji,
            "variants": variants,
            "individual_sha": individual,
        }
        (OUT / "filter_isolation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        compact = {
            "baseline": baseline["count"],
            "none": variants["none"]["count"],
            "day_ji_only": variants["day_ji_only"]["count"],
            "all_sha_only": variants["all_sha_only"]["count"],
            "combined": variants["baseline"]["count"],
            "individual": {
                k: {"count": v["count"], "excluded": v["excluded_count"]}
                for k, v in individual.items()
            },
        }
        print(json.dumps(compact, ensure_ascii=False))
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
