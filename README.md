# SelectDatWeb

复刻“择日大师”内部功能的 HTML + Python 版本。当前先实现 **山家择日**，不包含原站登录系统。

## 运行

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

浏览器打开 `http://127.0.0.1:5000`。

## 当前已实现

- 原站风格：顶部日期/时辰栏、中间日课区、左侧月煞/年煞提示、右侧输入区、底部功能栏。
- 原站公开前端中的二十四山编号、方位和五行。
- 坐卦 / 二十四山联动。
- 兼山：兼右、正针、兼左。
- 120 分金：按原站 24 山到 12 地支的五分金结构生成。
- 用事：建造、进神、安门、修方、安葬、入宅、开业、作灶等原站选项。
- 福主年命：支持输入公历年份或干支。
- 原站公开“利月”规则：
  - 寅卯：木火山有利
  - 辰：土金山有利
  - 巳午：火土山有利
  - 未：土山有利
  - 申酉：金水山有利
  - 戌：土金山有利
  - 亥子：水木山有利
  - 丑：土金山有利
- 四档结果筛选：1级大吉、2级小吉、3级日干生旺、4级日干次旺。
- 日柱/月柱/年柱、农历、时柱使用 `lunar_python` 计算。
- 五行生克、日支冲山、福主年命冲/六合/三合、年三煞、通胜宜忌参与结果计算。
- 12 时辰筛选和逐时干支/五行关系。

## API

### GET /api/options

返回二十四山、用事、筛选等级、时辰、利月等前端数据。

### POST /api/calculate

示例：

```json
{
  "start_date": "2026-09-28",
  "end_date": "2026-10-08",
  "use_type": "建造",
  "mountain_id": 1,
  "life_years": "1988,1990",
  "favorable_months": [],
  "level": "小吉",
  "hours": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
}
```

## 规则一致性说明

能从目标站点公开 HTML/JavaScript 直接确认的数据，按其原值复刻，包括二十四山编号/五行、兼山结构、120 分金结构、用事列表、时辰和利月列表。

原站真正的最终日课评级权重在服务端 PHP 中，网页没有公开。当前 Python 内核没有假装获得那部分私有源码，而是使用已公开规则，加上正体五行常用的生克、冲合、三煞、通胜宜忌形成可执行评级。后续如果用同一组输入拿到原站输出样本，可以继续做差分校准，让评级结果进一步逼近原站。

> 本项目实现的是传统民俗择日逻辑，不应替代建筑、施工、安全、法律或医疗等专业判断。


## 原站黑盒对照采样

为了校准原站服务端没有公开的日课判定规则，项目包含 `tools/capture_reference.py`。
脚本使用普通 HTTP Session、标准浏览器请求头和固定请求间隔访问，不做 CAPTCHA 绕过、指纹伪装或代理轮换。

Windows CMD：

```bat
set ZERIDASHI_PHONE=你的手机号
set ZERIDASHI_PASSWORD=你的密码
python tools\capture_reference.py
```

PowerShell：

```powershell
$env:ZERIDASHI_PHONE="你的手机号"
$env:ZERIDASHI_PASSWORD="你的密码"
python tools/capture_reference.py
```

输出位于 `reference_capture/<时间戳>/`，该目录已加入 `.gitignore`。脚本会在写文件前脱敏手机号和密码，也不会保存 Session Cookie。
