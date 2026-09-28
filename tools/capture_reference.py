from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests


BASE_URL = os.getenv("ZERIDASHI_BASE_URL", "http://zeridashi.top").rstrip("/")
PHONE = os.getenv("ZERIDASHI_PHONE", "").strip()
PASSWORD = os.getenv("ZERIDASHI_PASSWORD", "").strip()
REQUEST_INTERVAL = float(os.getenv("ZERIDASHI_REQUEST_INTERVAL", "1.5"))
OUT_ROOT = Path(os.getenv("ZERIDASHI_CAPTURE_DIR", "reference_capture"))


class FormParser(HTMLParser):
    def __init__(self, form_id: str | None = None):
        super().__init__()
        self.form_id = form_id
        self.in_form = False
        self.action = ""
        self.method = "get"
        self.inputs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k: (v or "") for k, v in attrs}
        if tag.lower() == "form":
            if self.form_id is None or data.get("id") == self.form_id or data.get("name") == self.form_id:
                self.in_form = True
                self.action = data.get("action", "")
                self.method = data.get("method", "get").lower()
        elif self.in_form and tag.lower() == "input":
            name = data.get("name")
            if name:
                self.inputs[name] = data.get("value", "")

    def handle_endtag(self, tag: str) -> None:
        if self.in_form and tag.lower() == "form":
            self.in_form = False


def redact(text: str) -> str:
    if PASSWORD:
        text = text.replace(PASSWORD, "<PASSWORD>")
    if PHONE:
        text = text.replace(PHONE, "<PHONE>")
    return text


class BrowserSession:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/154.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Connection": "keep-alive",
            }
        )

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = path if path.startswith("http") else urljoin(BASE_URL + "/", path.lstrip("/"))
        response = self.session.request(method, url, timeout=30, allow_redirects=True, **kwargs)
        response.raise_for_status()
        if REQUEST_INTERVAL > 0:
            time.sleep(REQUEST_INTERVAL)
        return response


def require_credentials() -> None:
    if not PHONE or not PASSWORD:
        raise SystemExit(
            "请先设置环境变量 ZERIDASHI_PHONE 和 ZERIDASHI_PASSWORD。"
        )


def login(browser: BrowserSession) -> tuple[requests.Response, dict[str, Any]]:
    login_page = browser.request(
        "GET", f"/zeridashi/index-web/login.php?id={PHONE}"
    )

    verify = browser.request(
        "POST",
        "/zeridashi/index-web/loginajax.php",
        data={
            "Action": "ChaXunDianHua",
            "dianhua": PHONE,
            "pwd": PASSWORD,
            "shebei": "",
        },
        headers={"Referer": login_page.url, "X-Requested-With": "XMLHttpRequest"},
    )
    try:
        verify_json = verify.json()
    except ValueError as exc:
        raise RuntimeError(f"登录校验接口没有返回 JSON：{redact(verify.text[:500])}") from exc

    state = str(verify_json.get("shenhe", ""))
    if state != "KeYiDengLu":
        raise RuntimeError(f"登录校验未通过：{redact(json.dumps(verify_json, ensure_ascii=False))}")

    parser = FormParser("loginform")
    parser.feed(login_page.text)
    payload = dict(parser.inputs)
    payload.update(
        {
            "Action": payload.get("Action") or "login",
            "dianhua": PHONE,
            "pwd": PASSWORD,
            "shebei": payload.get("shebei", ""),
            "ipaddr": payload.get("ipaddr", ""),
            "ip": payload.get("ip", ""),
            "scrollWidth": payload.get("scrollWidth", "1920"),
            "scrollHeight": payload.get("scrollHeight", "1080"),
        }
    )
    action = parser.action or "/zeridashi/index-web/login.php"
    logged = browser.request(
        "POST",
        action,
        data=payload,
        headers={"Referer": login_page.url},
    )

    if "请先登录" in logged.text and "login.php" in logged.text:
        raise RuntimeError("登录表单提交后仍被判定为未登录。")

    return logged, verify_json


def save_text(folder: Path, name: str, response: requests.Response) -> None:
    text = redact(response.text)
    (folder / name).write_text(text, encoding="utf-8")


def extract_user_yz(html: str) -> str:
    patterns = [
        r"function\s+user_yz\s*\([^)]*\)\s*\{.*?\n\}",
        r"function\s+user_yz\s*\([^)]*\)\s*\{.*?\}",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.S)
        if match:
            return redact(match.group(0))
    return ""


def main() -> int:
    require_credentials()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = OUT_ROOT / stamp
    folder.mkdir(parents=True, exist_ok=True)

    browser = BrowserSession()
    logged, verify_json = login(browser)

    targets = {
        "index.html": f"/index-web.php?id={PHONE}",
        "topzeri.html": "/zeridashi/yixue/topzeri.php",
        "topzeri_info.html": "/zeridashi/yixue/topzeri_info.php",
        "zeri.html": "/zeridashi/yixue/zeri.php",
        "topzeri.js": "/zeridashi/inc/topzeri.js?ver=123456",
        "zeri.js": "/zeridashi/yixue/zeri.js?ver=123456",
    }

    report: dict[str, Any] = {
        "login_state": verify_json.get("shenhe"),
        "captured_at": stamp,
        "base_url": BASE_URL,
        "pages": {},
    }

    # Preserve the response reached after login as a useful diagnostic page.
    save_text(folder, "login_result.html", logged)

    zeri_text = ""
    for name, path in targets.items():
        response = browser.request("GET", path, headers={"Referer": logged.url})
        save_text(folder, name, response)
        report["pages"][name] = {
            "status": response.status_code,
            "url": redact(response.url),
            "bytes": len(response.content),
            "contains_login_prompt": "请先登录" in response.text,
        }
        if name == "zeri.html":
            zeri_text = response.text

    user_yz = extract_user_yz(zeri_text)
    (folder / "user_yz.txt").write_text(user_yz, encoding="utf-8")

    parser = FormParser("form1")
    parser.feed(zeri_text)
    safe_inputs = {
        key: redact(value)
        for key, value in parser.inputs.items()
        if key not in {"pwd", "password"}
    }
    (folder / "zeri_form.json").write_text(
        json.dumps(
            {
                "action": parser.action,
                "method": parser.method,
                "inputs": safe_inputs,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (folder / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"抓取完成：{folder}")
    print("密码、手机号不会写入输出文件。")
    if user_yz:
        print("已提取登录后 centerFrame 的 user_yz()，可继续确定实际计算提交链路。")
    else:
        print("未在 zeri.html 中找到 user_yz()，请检查 report.json。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        print(f"网络请求失败：{exc}", file=sys.stderr)
        raise SystemExit(2)
    except Exception as exc:
        print(f"抓取失败：{redact(str(exc))}", file=sys.stderr)
        raise SystemExit(1)
