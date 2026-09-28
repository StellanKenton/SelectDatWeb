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
OUT = Path("reference_browser")
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
            return option.get_attribute("value")
    raise RuntimeError(f"{element_id} 找不到包含 {text!r} 的选项")


def login(driver):
    driver.get(f"{BASE}/zeridashi/index-web/login.php?id={PHONE}")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "dianhua"))
    ).send_keys(PHONE)
    driver.find_element(By.ID, "pwd").send_keys(PASSWORD)
    driver.find_element(By.ID, "loginbutton").click()

    # artDialog confirmation used by the original page.
    deadline = time.time() + 12
    clicked = False
    while time.time() < deadline and not clicked:
        for xp in [
            "//button[contains(normalize-space(.),'确定')]",
            "//a[contains(normalize-space(.),'确定')]",
            "//*[contains(@class,'aui_state_highlight')]",
        ]:
            try:
                els = driver.find_elements(By.XPATH, xp)
                for el in els:
                    if el.is_displayed():
                        el.click()
                        clicked = True
                        break
            except Exception:
                pass
            if clicked:
                break
        if not clicked:
            time.sleep(0.2)

    if not clicked:
        raise RuntimeError("未找到原站登录确认按钮")

    WebDriverWait(driver, 30).until(
        lambda d: len(d.find_elements(By.NAME, "top1Frame")) > 0
    )


def capture_initial_center(driver):
    wait_frame(driver, "centerFrame")
    WebDriverWait(driver, 30).until(
        lambda d: "显示：" in d.page_source and "个日课" in d.page_source
    )
    time.sleep(0.8)
    html = redact(driver.page_source)
    text = redact(driver.find_element(By.TAG_NAME, "body").text)
    (OUT / "center_initial.html").write_text(html, encoding="utf-8")
    (OUT / "center_initial.txt").write_text(text, encoding="utf-8")
    m = re.search(r"显示：\s*(\d+)个日课", text)
    return int(m.group(1)) if m else -1


def configure_and_search(driver):
    # Top date/ganzhi bar.
    wait_frame(driver, "top1Frame")
    select_value(driver, "rilitype", "干支")
    select_value(driver, "ganzhinian", "163")
    month_seq = select_text_contains(driver, "ganzhiyue", "丁酉")
    select_value(driver, "ganzhiri", "全部")

    # Input panel: execute the site's own change handlers so all hidden
    # filters are filled exactly as the original UI would do.
    wait_frame(driver, "shuruFrame")
    select_value(driver, "yiji", "all")
    select_value(driver, "yongshi", "0")
    select_value(driver, "zuobagua", "1")
    time.sleep(0.5)
    select_value(driver, "ershisishan", "1")
    time.sleep(0.5)
    select_value(driver, "jian", "亥巳")
    select_value(driver, "fenjin", "乙亥")
    select_value(driver, "dagua", "2;2")
    time.sleep(0.5)

    base_state = driver.execute_script(
        """
        const ids=['yiji','yongshi','yongshiType','zuobagua','ershisishan',
          'jian','fenjin','dagua','xiufang','nianming','wangming',
          'mingshaguolv','huamingshaguolv','yueli','xiongsha','jxiongsha',
          'rijishi0','rijishi1','rijishi2','rijishi3'];
        const out={};
        for (const id of ids) {
          const el=document.getElementById(id);
          out[id]=el ? (el.value || '') : null;
        }
        return out;
        """
    )
    base_state["ganzhiyue_seq"] = month_seq
    (OUT / "configured_state.json").write_text(
        redact(json.dumps(base_state, ensure_ascii=False, indent=2)),
        encoding="utf-8",
    )

    counts = {}
    for level in ["全部", "大吉", "小吉", "生旺", "耗"]:
        wait_frame(driver, "shuruFrame")
        select_value(driver, "paichubiaozhi", level)
        time.sleep(0.35)
        driver.execute_script("toframes();")

        wait_frame(driver, "centerFrame")
        WebDriverWait(driver, 45).until(
            lambda d: "显示：" in d.page_source and "个日课" in d.page_source
        )
        time.sleep(1.1)

        html = redact(driver.page_source)
        text_body = redact(driver.find_element(By.TAG_NAME, "body").text)
        safe = {"全部": "all", "大吉": "daji", "小吉": "xiaoji", "生旺": "shengwang", "耗": "hao"}[level]
        (OUT / f"center_result_{safe}.html").write_text(html, encoding="utf-8")
        (OUT / f"center_result_{safe}.txt").write_text(text_body, encoding="utf-8")
        m = re.search(r"显示：\s*(\d+)个日课", text_body)
        counts[level] = int(m.group(1)) if m else -1
        time.sleep(1.2)

    return counts, base_state


def main() -> int:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1820,800")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        login(driver)
        initial_count = capture_initial_center(driver)
        counts, state = configure_and_search(driver)

        driver.switch_to.default_content()
        driver.save_screenshot(str(OUT / "reference_page.png"))

        result = {
            "ok": True,
            "initial_result_count": initial_count,
            "result_counts": counts,
            "yongshi": state.get("yongshi"),
            "mountain": state.get("ershisishan"),
            "jian": state.get("jian"),
            "fenjin": state.get("fenjin"),
            "dagua": state.get("dagua"),
            "day_ji": [state.get("rijishi0"), state.get("rijishi1"), state.get("rijishi2"), state.get("rijishi3")],
            "xiongsha": state.get("xiongsha"),
            "yiji": state.get("yiji"),
        }
        (OUT / "summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
