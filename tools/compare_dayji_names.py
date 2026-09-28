from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path("main_src").resolve()))
from lunar_python import Solar  # noqa: E402


def safe_list(obj, method: str) -> list[str]:
    fn = getattr(obj, method)
    return [str(x) for x in (fn() or [])]


def main() -> int:
    rows = []
    d = date(2026, 9, 7)
    end = date(2026, 10, 8)
    while d <= end:
        lunar = Solar.fromYmd(d.year, d.month, d.day).getLunar()
        rows.append({
            "date": d.isoformat(),
            "ganzhi": lunar.getEightChar().getDay(),
            "yi": safe_list(lunar, "getDayYi"),
            "ji": safe_list(lunar, "getDayJi"),
        })
        d += timedelta(days=1)
    Path("reference_isolation").mkdir(exist_ok=True)
    Path("reference_isolation/lunar_python_yiji.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for row in rows:
        print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
