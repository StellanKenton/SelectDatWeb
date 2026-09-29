"""Regression for the visible 2026-09-08 坤山斗首 card."""

import unittest

from core.shanjia import calculate_days


class DoushouDisplayTest(unittest.TestCase):
    def test_kun_card_matches_visible_reference_fields(self):
        data = calculate_days({
            "start_date": "2026-09-08",
            "end_date": "2026-09-08",
            "evaluation_mode": True,
            "mountain_id": 17,
            "jian": "未丑",
            "hours": [0],
        })
        self.assertEqual(data["count"], 1)
        card = data["results"][0]
        self.assertEqual(card["reference_grade_label"], "五行欠吉")
        self.assertEqual(card["pillar_top_relations"], ["泄", "泄", "克", "泄"])
        self.assertEqual(card["pillar_bottom_relations"], ["泄", "令", "克", "生"])
        self.assertEqual(card["pillar_nayin_elements"], ["水", "火", "水", "水"])
        self.assertEqual(card["hour_signs"], ["时吉", "罗纹", "司命", "阴贵"])
        self.assertEqual(card["shan_sha_labels"],
                         ["山运水", "活阴府", "年正阴府", "时正阴府", "时兼三杀"])
        self.assertEqual(card["zhoutang"], "香火宜 · 入宅宜")
        self.assertEqual(card["master_sha_labels"], ["日冲卯命", "时冲午命"])
        other_jian = calculate_days({
            "start_date": "2026-09-08", "end_date": "2026-09-08",
            "evaluation_mode": True, "mountain_id": 17,
            "jian": "申寅", "hours": [0],
        })["results"][0]
        self.assertNotIn("时兼三杀", other_jian["shan_sha_labels"])


if __name__ == "__main__":
    unittest.main()
