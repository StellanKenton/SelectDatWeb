"""Compare locally calculated 斗首 rows with saved visible original-site cards."""

import json
from pathlib import Path
import unittest

from core.doushou import calculate_doushou


ROOT = Path(__file__).resolve().parents[1]
CAPTURES = (
    ("visual_reference_dingyou_2026.json", "壬", 31),
    ("B07_no_month_time_sansha_reference.json", "丙", 1),
    ("visual_reference_jia_2026.json", "甲", 31),
    ("visual_reference_gen_2026.json", "艮", 31),
    ("visual_reference_geng_2026.json", "庚", 31),
)


class DoushouParityTest(unittest.TestCase):
    def test_visible_cards_match_eight_doushou_rows(self):
        checked = 0
        for filename, mountain, count in CAPTURES:
            source = json.loads((ROOT / "output" / filename).read_text(encoding="utf-8"))
            cards = source["center_text"].split("[打印] ")[1:]
            self.assertEqual(len(cards), count, filename)
            for card in cards:
                block = card.split("\n斗首择日\n", 1)[1].split("\n" + mountain + "山煞", 1)[0].splitlines()
                with self.subTest(source=filename, day=card[:35]):
                    self.assertEqual(len(block), 34)
                    pillars = tuple(block[8 + i] + block[12 + i] for i in range(4))
                    calculated = calculate_doushou(mountain, pillars)
                    rows = calculated["pillars"]
                    expected = []
                    for field in ("upper_star", "upper_element", "upper_stage",
                                  "lower_star", "lower_element", "lower_stage"):
                        expected.extend(row[field] for row in rows)
                    observed = block[0:8] + block[16:32]
                    self.assertEqual(observed, expected)
                    self.assertEqual(block[32:], ["山", mountain + "山斗首属 " + calculated["mountain_element"]])
                    checked += 1
        self.assertEqual(checked, 125)


if __name__ == "__main__":
    unittest.main()
