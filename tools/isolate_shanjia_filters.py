from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoSuchFrameException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = os.getenv("ZERIDASHI_BASE_URL", "http://zeridashi.top").rstrip("/")
PHONE = os.environ["ZERIDASHI_PHONE"]
PASSWORD = os.environ["ZERIDASHI_PASSWORD"]
OUT = Path("reference_isolation")
OUT.mkdir(parents=True, exist_ok=True)

REQUEST_PAUSE = 1.6


def wait_frame(driver, name: str, timeout: float = 30.0) -> None:
    driver.switch_to.default_content()
    WebDriverWait(driver, timeout).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, name))
    )


def select_value(driver, element_id: str, value: str) -> None:
    el = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    Select(el).select_by_value(value)
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", el
    )


def select_text_contains(driver, element_id: str, text: str) -> str:
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


def login(driver) -> None:
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
            try:
                for el in driver.find_elements(By.XPATH, xp):
                    if el.is_displayed():
                        el.click()
                        clicked = True
                        break
            except WebDriverException:
                pass
            if clicked:
                break
        if not clicked:
            time.sleep(0.25)
    if not clicked:
        raise RuntimeError("登录确认按钮未出现")

    WebDriverWait(driver, 30).until(
        lambda d: len(d.find_elements(By.NAME, "top1Frame")) > 0
    )


def configure(driver) -> tuple[list[str], list[str]]:
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
          all_sha: boxes.map(x=>x.value),
          checked_sha: boxes.filter(x=>x.checked).map(x=>x.value),
          day_ji: [0,1,2,3].map(i => {
            const e=document.getElementById('rijishi'+i);
            return e ? (e.value || '') : '';
          })
        };
        """
    )
    return list(state["checked_sha"]), [x for x in state["day_ji"] if x]


def set_filters(driver, sha_values: list[str], day_ji: list[str]) -> None:
    wait_frame(driver, "shuruFrame")
    select_value(driver, "paichubiaozhi", "全部")
    driver.execute_script(
        """
        const wanted=new Set(arguments[0]);
        document.querySelectorAll("input[name='Arry_xiongsha[]']").forEach(
          e => { e.checked = wanted.has(e.value); }
        );
        const ji=arguments[1];
        for(let i=0;i<4;i++){
          const e=document.getElementById('rijishi'+i);
          if(e) e.value = ji[i] || '';
        }
        """,
        sha_values,
        list(day_ji[:4]) + [""] * max(0, 4-len(day_ji)),
    )


def submit_center_only(driver) -> None:
    wait_frame(driver, "shuruFrame")
    WebDriverWait(driver, 25).until(
        lambda d: d.execute_script(
            """
            const c=parent.frames['centerFrame'];
            if(!c || !c.document) return false;
            const need=['Action','weizhi','ganzhiri','form1','yongshiType','yongshi',
              'zuobagua','ershisishan','jian','fenjin','dagua','daguaval','nianming',
              'wangming','mingshaguolv','huamingshaguolv','yueli','paichubiaozhi',
              'rijishi0','rijishi1','rijishi2','rijishi3','shenshawei1','shenshawei2',
              'xiongsha','jxiongsha','xiufang'];
            return need.every(id => c.document.getElementById(id));
            """
        )
    )
    driver.execute_script(
        """
        const c=parent.frames['centerFrame'].document;
        c.getElementById('Action').value='kaishisousuo';
        c.getElementById('weizhi').value='';
        c.getElementById('ganzhiri').value='全部';

        const copy=['yongshiType','yongshi','zuobagua','ershisishan','jian','fenjin',
          'nianming','wangming','mingshaguolv','huamingshaguolv','yueli',
          'paichubiaozhi','rijishi0','rijishi1','rijishi2','rijishi3',
          'shenshawei1','shenshawei2','xiufang'];
        for(const id of copy){
          const src=document.getElementById(id), dst=c.getElementById(id);
          if(src && dst) dst.value=src.value || '';
        }

        const dg=document.getElementById('dagua');
        if(dg){
          c.getElementById('daguaval').value=dg.value || '';
          c.getElementById('dagua').value=dg.options[dg.selectedIndex]?.text || '';
        }

        dClick();
        jdClick();
        c.getElementById('xiongsha').value=document.getElementById('xiongsha').value || '';
        c.getElementById('jxiongsha').value=document.getElementById('jxiongsha').value || '';
        c.getElementById('form1').submit();
        """
    )


def read_center_result(driver, timeout: float = 55.0) -> str:
    deadline=time.time()+timeout
    last_error=""
    while time.time() < deadline:
        try:
            driver.switch_to.default_content()
            frames=driver.find_elements(By.NAME, "centerFrame")
            if not frames:
                time.sleep(0.25)
                continue
            driver.switch_to.frame(frames[0])
            text=driver.execute_script(
                "return document.body ? (document.body.innerText || '') : '';"
            )
            if "显示：" in text and "个日课" in text:
                return text
        except (NoSuchFrameException, StaleElementReferenceException, WebDriverException) as exc:
            last_error=type(exc).__name__
        time.sleep(0.3)
    raise RuntimeError(f"centerFrame 结果等待超时: {last_error}")


def parse_result(text: str) -> dict:
    count_m=re.search(r"显示：\s*(\d+)个日课", text)
    pairs=[]
    for block in text.split("[打印]")[1:]:
        dm=re.search(r"公历:(\d+)月(\d+)日", block)
        hm=re.search(r"\n(\d{1,2})点\n时[吉凶]", block)
        if dm and hm:
            pairs.append(
                f"2026-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}T{int(hm.group(1)):02d}"
            )
    return {
        "count": int(count_m.group(1)) if count_m else -1,
        "pairs": pairs,
        "dates": sorted({p[:10] for p in pairs}),
    }


def run_variant(driver, sha_values: list[str], day_ji: list[str]) -> dict:
    set_filters(driver, sha_values, day_ji)
    submit_center_only(driver)
    driver.switch_to.default_content()
    time.sleep(0.9)
    text=read_center_result(driver)
    result=parse_result(text)
    time.sleep(REQUEST_PAUSE)
    return result


def main() -> int:
    opts=webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1820,800")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    driver=webdriver.Chrome(options=opts)
    try:
        login(driver)
        default_sha, default_day_ji=configure(driver)
        print("默认神煞数量:", len(default_sha), flush=True)

        none=run_variant(driver, [], [])
        day_ji_only=run_variant(driver, [], default_day_ji)
        all_sha_only=run_variant(driver, default_sha, [])
        baseline=run_variant(driver, default_sha, default_day_ji)

        none_pairs=set(none["pairs"])
        individual={}
        for i, rule in enumerate(default_sha):
            item=run_variant(driver, [rule], [])
            item["excluded_pairs"]=sorted(none_pairs-set(item["pairs"]))
            item["excluded_dates"]=sorted({x[:10] for x in item["excluded_pairs"]})
            individual[rule]=item
            print(
                f"{i+1:02d}/{len(default_sha)} {rule}: "
                f"count={item['count']} exclude={len(item['excluded_pairs'])}",
                flush=True,
            )

        result={
            "default_sha": default_sha,
            "default_day_ji": default_day_ji,
            "none": none,
            "day_ji_only": day_ji_only,
            "all_sha_only": all_sha_only,
            "baseline": baseline,
            "individual_sha": individual,
        }
        (OUT/"filter_isolation.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "none": none["count"],
                    "day_ji_only": day_ji_only["count"],
                    "all_sha_only": all_sha_only["count"],
                    "baseline": baseline["count"],
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
