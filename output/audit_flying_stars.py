"""Audit 60 saved monthly cards against installed lunar_python nine-star rules."""

from __future__ import annotations

import json
import re
from pathlib import Path

from lunar_python import Solar

HERE = Path(__file__).resolve().parent


def card_rows(name: str, year: int) -> list[dict]:
    source = json.loads((HERE / name).read_text(encoding="utf-8"))["center_text"]
    rows = []
    for card in source.split("[打印] ")[1:]:
        date = re.search(r"公历:(\d+)月(\d+)日", card)
        stars = {kind: re.search(rf"(?m)^([1-9]{{4}}){kind}$", card) for kind in ("向", "中", "坐")}
        if not date or any(value is None for value in stars.values()):
            continue
        month, day = (int(x) for x in date.groups())
        lunar = Solar.fromYmdHms(year, month, day, 0, 0, 0).getLunar()
        local = "".join(str(getter().getIndex() + 1) for getter in
                        (lunar.getYearNineStar, lunar.getMonthNineStar,
                         lunar.getDayNineStar, lunar.getTimeNineStar))
        site = {kind: value.group(1) for kind, value in stars.items()}
        shift = lambda text, amount: "".join(str((int(c) - 1 + amount) % 9 + 1) for c in text)
        rows.append({"date": f"{year}-{month:02d}-{day:02d}", "site": site,
                     "lunar_python_center": local,
                     "center_equal": site["中"] == local,
                     "seat_shift_5_equal": site["坐"] == shift(site["中"], 5),
                     "facing_shift_4_equal": site["向"] == shift(site["中"], 4),
                     "digit_equal": [a == b for a, b in zip(site["中"], local)]})
    return rows


def main() -> None:
    rows = card_rows("B01_reference.json", 2011) + card_rows("B02_reference.json", 2026)
    report = {
        "total_cards": len(rows),
        "by_year": {},
        "all_seat_shift_5": all(r["seat_shift_5_equal"] for r in rows),
        "all_facing_shift_4": all(r["facing_shift_4_equal"] for r in rows),
        "rows": rows,
    }
    for year in (2011, 2026):
        subset = [r for r in rows if r["date"].startswith(str(year))]
        report["by_year"][year] = {
            "cards": len(subset),
            "center_full_equal": sum(r["center_equal"] for r in subset),
            "year_month_day_time_digit_equal": [sum(r["digit_equal"][i] for r in subset) for i in range(4)],
        }
    (HERE / "flying_star_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("total_cards", "by_year", "all_seat_shift_5", "all_facing_shift_4")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
