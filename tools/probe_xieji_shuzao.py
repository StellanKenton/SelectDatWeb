from __future__ import annotations

import json
from datetime import date, timedelta

from lunar_python import Solar
import cnlunar

ORIGINAL = {
    "2026-09-07": "J", "2026-09-08": "Y", "2026-09-09": "J",
    "2026-09-10": "Y", "2026-09-11": "J", "2026-09-12": "Y",
    "2026-09-13": "Y", "2026-09-14": "X", "2026-09-15": "N",
    "2026-09-16": "Y", "2026-09-17": "J", "2026-09-18": "Y",
    "2026-09-19": "J", "2026-09-20": "J", "2026-09-21": "J",
    "2026-09-22": "X", "2026-09-23": "Y", "2026-09-24": "J",
    "2026-09-25": "Y", "2026-09-26": "X", "2026-09-27": "J",
    "2026-09-28": "Y", "2026-09-29": "J", "2026-09-30": "J",
    "2026-10-01": "J", "2026-10-02": "X", "2026-10-03": "Y",
    "2026-10-04": "Y", "2026-10-05": "J", "2026-10-06": "Y",
    "2026-10-07": "J", "2026-10-08": "X",
}

def safe_list(obj, name):
    fn=getattr(obj,name,None)
    if not callable(fn):
        return []
    try:
        return [str(x) for x in (fn() or [])]
    except Exception:
        return []

d=date(2026,9,7)
end=date(2026,10,8)
while d<=end:
    lunar=Solar.fromYmd(d.year,d.month,d.day).getLunar()
    ec=lunar.getEightChar()
    xj = cnlunar.Lunar(__import__("datetime").datetime(d.year,d.month,d.day,12,0), godType="8char")
    row={
        "date":d.isoformat(),
        "original":ORIGINAL[d.isoformat()],
        "ganzhi":ec.getDay(),
        "month_ganzhi":ec.getMonth(),
        "zhi_xing":str(lunar.getZhiXing()),
        "ji_shen":safe_list(lunar,"getDayJiShen"),
        "xiong_sha":safe_list(lunar,"getDayXiongSha"),
        "yi":safe_list(lunar,"getDayYi"),
        "ji":safe_list(lunar,"getDayJi"),
        "cn_good": list(xj.goodThing),
        "cn_bad": list(xj.badThing),
        "cn_level": str(xj.todayLevelName),
        "cn_good_gods": list(xj.goodGodName),
        "cn_bad_gods": list(xj.badGodName),
    }
    print(json.dumps(row,ensure_ascii=False))
    d+=timedelta(days=1)
