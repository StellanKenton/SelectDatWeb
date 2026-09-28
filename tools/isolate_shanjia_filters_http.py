from __future__ import annotations

import json
import os
import re
import time
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = os.getenv("ZERIDASHI_BASE_URL", "http://zeridashi.top").rstrip("/")
PHONE = os.environ["ZERIDASHI_PHONE"]
PASSWORD = os.environ["ZERIDASHI_PASSWORD"]
OUT = Path("reference_http_isolation")
OUT.mkdir(parents=True, exist_ok=True)
PAUSE = 1.8


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
    raise RuntimeError(f"{element_id} 找不到 {text!r}")


def login(driver):
    driver.get(f"{BASE}/zeridashi/index-web/login.php?id={PHONE}")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "dianhua"))
    ).send_keys(PHONE)
    driver.find_element(By.ID, "pwd").send_keys(PASSWORD)
    driver.find_element(By.ID, "loginbutton").click()

    deadline = time.time() + 15
    clicked = False
    while time.time() < deadline and not clicked:
        for xp in (
            "//button[contains(normalize-space(.),'确定')]",
            "//a[contains(normalize-space(.),'确定')]",
            "//*[contains(@class,'aui_state_highlight')]",
        ):
            for el in driver.find_elements(By.XPATH, xp):
                if el.is_displayed():
                    el.click()
                    clicked = True
                    break
            if clicked:
                break
        if not clicked:
            time.sleep(0.25)
    if not clicked:
        raise RuntimeError("登录确认按钮未出现")
    WebDriverWait(driver, 30).until(
        lambda d: len(d.find_elements(By.NAME, "top1Frame")) > 0
    )


def configure_and_search(driver):
    wait_frame(driver, "top1Frame")
    select_value(driver, "rilitype", "干支")
    select_value(driver, "ganzhinian", "163")
    select_text_contains(driver, "ganzhiyue", "丁酉")
    select_value(driver, "ganzhiri", "全部")

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
    select_value(driver, "paichubiaozhi", "全部")
    time.sleep(0.6)

    state = driver.execute_script(
        """
        const boxes=[...document.querySelectorAll("input[name='Arry_xiongsha[]']")];
        return {
          checked_sha: boxes.filter(x=>x.checked).map(x=>x.value),
          day_ji: [0,1,2,3].map(i => {
            const e=document.getElementById('rijishi'+i);
            return e ? (e.value || '') : '';
          })
        };
        """
    )

    # First search is the site's exact normal UI flow.
    driver.execute_script("toframes();")
    driver.switch_to.default_content()
    WebDriverWait(driver, 50).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, "centerFrame"))
    )
    WebDriverWait(driver, 50).until(
        lambda d: "显示：" in d.page_source and "个日课" in d.page_source
    )
    time.sleep(1.2)

    form = driver.execute_script(
        """
        const f=document.getElementById('form1');
        const pairs=[];
        for(const e of f.elements){
          if(!e.name) continue;
          if((e.type==='checkbox'||e.type==='radio') && !e.checked) continue;
          if(e.tagName==='SELECT' && e.multiple){
            for(const o of e.selectedOptions) pairs.push([e.name,o.value]);
          } else {
            pairs.push([e.name,e.value || '']);
          }
        }
        return {
          action: f.getAttribute('action') || '',
          pairs: pairs,
          text: document.body ? document.body.innerText : ''
        };
        """
    )
    return state, form


def html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def parse_result(text: str) -> dict:
    count_m = re.search(r"显示：\s*(\d+)个日课", text)
    pairs = []
    for block in text.split("[打印]")[1:]:
        dm = re.search(r"公历:(\d+)月(\d+)日", block)
        hm = re.search(r"\n\s*(\d{1,2})点\s*\n\s*时[吉凶]", block)
        if dm and hm:
            pairs.append(
                f"2026-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}T{int(hm.group(1)):02d}"
            )
    return {
        "count": int(count_m.group(1)) if count_m else -1,
        "pair_count": len(pairs),
        "pairs": pairs,
        "dates": sorted({p[:10] for p in pairs}),
    }


def replace_fields(base_pairs: list[list[str]], updates: dict[str, str]) -> list[tuple[str, str]]:
    names = set(updates)
    out = [(str(k), str(v)) for k, v in base_pairs if k not in names]
    out.extend((k, v) for k, v in updates.items())
    return out


def make_session(driver) -> requests.Session:
    session = requests.Session()
    ua = driver.execute_script("return navigator.userAgent")
    session.headers.update(
        {
            "User-Agent": ua,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
        }
    )
    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"])
    return session


def run_post(
    session: requests.Session,
    action: str,
    base_pairs: list[list[str]],
    name: str,
    sha_values: list[str],
    day_ji: list[str],
) -> dict:
    updates = {
        "Action": "kaishisousuo",
        "paichubiaozhi": "全部",
        "xiongsha": ";".join(sha_values),
        "rijishi0": day_ji[0] if len(day_ji) > 0 else "",
        "rijishi1": day_ji[1] if len(day_ji) > 1 else "",
        "rijishi2": day_ji[2] if len(day_ji) > 2 else "",
        "rijishi3": day_ji[3] if len(day_ji) > 3 else "",
    }
    payload = replace_fields(base_pairs, updates)
    url = urljoin(BASE + "/", action.lstrip("/")) if action else f"{BASE}/zeridashi/yixue/zeri.php"
    response = session.post(
        url,
        data=payload,
        timeout=45,
        allow_redirects=True,
        headers={"Referer": f"{BASE}/zeridashi/yixue/zeri.php"},
    )
    response.raise_for_status()
    safe_html = redact(response.text)
    text = redact(html_to_text(response.text))
    (OUT / f"{name}.html").write_text(safe_html, encoding="utf-8")
    (OUT / f"{name}.txt").write_text(text, encoding="utf-8")
    result = parse_result(text)
    result["status"] = response.status_code
    result["login_prompt"] = "请先登录" in text or "使用前请先点击顶部【登录】" in text
    time.sleep(PAUSE)
    return result


def main() -> int:
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1820,800")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=opts)
    try:
        login(driver)
        state, form = configure_and_search(driver)
        default_sha = list(state["checked_sha"])
        default_day_ji = [x for x in state["day_ji"] if x]
        browser_baseline = parse_result(str(form["text"]))

        session = make_session(driver)
        action = str(form["action"] or "/zeridashi/yixue/zeri.php")
        base_pairs = list(form["pairs"])

        baseline = run_post(session, action, base_pairs, "baseline", default_sha, default_day_ji)
        if baseline["count"] != browser_baseline["count"]:
            raise RuntimeError(
                f"HTTP复放与浏览器基线不一致: browser={browser_baseline['count']} http={baseline['count']}"
            )

        none = run_post(session, action, base_pairs, "none", [], [])
        day_ji_only = run_post(session, action, base_pairs, "day_ji_only", [], default_day_ji)
        all_sha_only = run_post(session, action, base_pairs, "all_sha_only", default_sha, [])

        none_pairs = set(none["pairs"])
        individual = {}
        for i, rule in enumerate(default_sha):
            item = run_post(session, action, base_pairs, f"sha_{i:02d}", [rule], [])
            excluded = sorted(none_pairs - set(item["pairs"]))
            item["excluded_pairs"] = excluded
            item["excluded_dates"] = sorted({x[:10] for x in excluded})
            individual[rule] = item
            print(
                f"{i+1:02d}/{len(default_sha)} {rule}: "
                f"count={item['count']} exclude={len(excluded)}",
                flush=True,
            )

        result = {
            "browser_baseline": browser_baseline,
            "default_sha": default_sha,
            "default_day_ji": default_day_ji,
            "baseline": baseline,
            "none": none,
            "day_ji_only": day_ji_only,
            "all_sha_only": all_sha_only,
            "individual_sha": individual,
        }
        (OUT / "filter_isolation.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "browser": browser_baseline["count"],
                    "baseline": baseline["count"],
                    "none": none["count"],
                    "day_ji_only": day_ji_only["count"],
                    "all_sha_only": all_sha_only["count"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
