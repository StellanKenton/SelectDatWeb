from __future__ import annotations

import json
import os
import re
import time
from html.parser import HTMLParser
from pathlib import Path

import requests
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


class FormSnapshot(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_form = False
        self.in_select = False
        self.select_name = ""
        self.select_value = None
        self.fields: list[tuple[str, str]] = []
        self.action = "/zeridashi/yixue/zeri.php"

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form" and a.get("id") == "form1":
            self.in_form = True
            self.action = a.get("action") or self.action
            return
        if not self.in_form:
            return
        if tag == "input":
            name = a.get("name")
            if not name:
                return
            typ = (a.get("type") or "text").lower()
            if typ in {"checkbox", "radio"} and "checked" not in a:
                return
            self.fields.append((name, a.get("value") or ""))
        elif tag == "select":
            self.in_select = True
            self.select_name = a.get("name") or ""
            self.select_value = None
        elif tag == "option" and self.in_select and "selected" in a:
            self.select_value = a.get("value") or ""

    def handle_endtag(self, tag):
        if tag == "select" and self.in_select:
            if self.select_name:
                self.fields.append((self.select_name, self.select_value or ""))
            self.in_select = False
            self.select_name = ""
            self.select_value = None
        elif tag == "form" and self.in_form:
            self.in_form = False


def form_snapshot(html: str) -> FormSnapshot:
    parser = FormSnapshot()
    parser.feed(html)
    return parser


def browser_session(driver) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": driver.execute_script("return navigator.userAgent"),
        "Referer": f"{BASE}/zeridashi/yixue/zeri.php",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    for cookie in driver.get_cookies():
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain") or "zeridashi.top",
            path=cookie.get("path") or "/",
        )
    return session


def mutate_fields(
    base_fields: list[tuple[str, str]],
    sha_values: list[str],
    day_ji: list[str],
) -> list[tuple[str, str]]:
    replacements = {
        "Action": "kaishisousuo",
        "paichubiaozhi": "全部",
        "xiongsha": ";".join(sha_values),
        "rijishi0": day_ji[0] if len(day_ji) > 0 else "",
        "rijishi1": day_ji[1] if len(day_ji) > 1 else "",
        "rijishi2": day_ji[2] if len(day_ji) > 2 else "",
        "rijishi3": day_ji[3] if len(day_ji) > 3 else "",
    }
    seen = set()
    fields: list[tuple[str, str]] = []
    for name, value in base_fields:
        if name in replacements:
            if name not in seen:
                fields.append((name, replacements[name]))
                seen.add(name)
            continue
        fields.append((name, value))
    for name, value in replacements.items():
        if name not in seen:
            fields.append((name, value))
    return fields


def fetch_variant(
    session: requests.Session,
    action: str,
    base_fields: list[tuple[str, str]],
    sha_values: list[str],
    day_ji: list[str],
) -> str:
    url = action if action.startswith("http") else BASE + action
    response = session.post(
        url,
        data=mutate_fields(base_fields, sha_values, day_ji),
        timeout=45,
        allow_redirects=True,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return redact(response.text)



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
        snapshot = form_snapshot(baseline_html)
        if not snapshot.fields:
            raise RuntimeError("基准结果页未解析到 form1")
        hidden = {}
        for name, value in snapshot.fields:
            hidden[name] = value
        default_sha = [x for x in hidden.get("xiongsha", "").split(";") if x]
        default_ji = [hidden.get(f"rijishi{i}", "") for i in range(4)]
        default_ji = [x for x in default_ji if x]
        session = browser_session(driver)

        variants = {}
        plan = [
            ("none", [], []),
            ("day_ji_only", [], default_ji),
            ("all_sha_only", default_sha, []),
            ("baseline", default_sha, default_ji),
        ]
        for name, sha, ji in plan:
            html = fetch_variant(session, snapshot.action, snapshot.fields, sha, ji)
            variants[name] = parse_html(html)
            if variants[name]["count"] < 0:
                (OUT / f"debug_{name}.html").write_text(html, encoding="utf-8")
                variants[name]["debug_bytes"] = len(html.encode("utf-8"))
                variants[name]["debug_login"] = "使用前请先点击顶部【登录】" in html or "请先登录" in html
                title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
                variants[name]["debug_title"] = re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
            time.sleep(1.4)

        none_ids = set(variants["none"]["lesson_ids"])
        individual = {}
        for rule in default_sha:
            html = fetch_variant(session, snapshot.action, snapshot.fields, [rule], [])
            parsed = parse_html(html)
            if parsed["count"] < 0 and not (OUT / "debug_single_sha.html").exists():
                (OUT / "debug_single_sha.html").write_text(html, encoding="utf-8")
                parsed["debug_bytes"] = len(html.encode("utf-8"))
                parsed["debug_login"] = "使用前请先点击顶部【登录】" in html or "请先登录" in html
                title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
                parsed["debug_title"] = re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
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
