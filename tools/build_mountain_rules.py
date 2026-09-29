"""Transcribe machine-readable rows from the user's OCR Word mountain table.

The OCR has errors in some prose cells, so only complete, checkable columns are
used by the calculation.  This script never contacts the original website.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = next(Path(r"C:\Users\senki\Desktop\Destiny\Word").glob("二十四山造葬凶煞表*.docx"))
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
ELEMENT = "金木水火土"


def tables():
    with ZipFile(SOURCE) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    result = []
    for table in root.iter(W + "tbl"):
        rows = []
        for row in table.findall(W + "tr"):
            cells = []
            for cell in row.findall(W + "tc"):
                cells.append(" ".join("".join(t.text or "" for t in p.iter(W + "t"))
                                      for p in cell.iter(W + "p")).strip())
            rows.append(cells)
        result.append(rows)
    return result


def main():
    table = tables()
    mountains = {}
    for row in table[0][1:] + table[1]:
        name = row[0]
        flow = re.findall(f"[{GAN}][{ZHI}]", row[11])
        if len(flow) != 10:
            raise ValueError(f"日流太岁 OCR token count: {name} {flow}")
        mountains[name] = {
            "sansha_branches": [x for x in ZHI if x in row[2]],
            "day_flow_taisui": flow,
            "day_xiaomie_note": row[7],
            "jian_clash_note": row[1],
        }
    if len(mountains) != 24:
        raise ValueError(f"Expected 24 mountain rows, got {len(mountains)}")
    year_group = {}
    groups = []
    for header in table[2][0][1:]:
        match = re.match(rf"([{ELEMENT}])山：\s*(.*)", header)
        if not match:
            raise ValueError(header)
        groups.append(match.group(2).replace(" ", ""))
    for row in table[2][1:]:
        gan_pair = row[0][0:2]
        for names, cell in zip(groups, row[1:]):
            value = cell.strip()[-1]
            if value not in ELEMENT:
                raise ValueError(f"山运 OCR element: {row[0]} {cell}")
            for name in names:
                year_group.setdefault(name, {})[gan_pair] = value
    if set(year_group) != set(mountains):
        raise ValueError(f"Mountain mismatch: {set(year_group) ^ set(mountains)}")
    nayin = {}
    for row in table[3]:
        for cell in row:
            match = re.search(f"([{GAN}][{ZHI}]).*([{ELEMENT}])", cell)
            if not match:
                raise ValueError(f"纳音 OCR cell: {cell}")
            nayin[match.group(1)] = match.group(2)
    if len(nayin) != 60:
        raise ValueError(f"Expected 60 纳音 rows, got {len(nayin)}")
    target = ROOT / "core" / "mountain_rule_reference.json"
    target.write_text(json.dumps({
        "source": SOURCE.name,
        "mountains": mountains,
        "shan_yun_by_year_gan_pair": year_group,
        "nayin_by_ganzhi": nayin,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote 24 mountains, 5 year groups and 60 纳音 rows to {target}")


if __name__ == "__main__":
    main()
