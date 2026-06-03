import unittest

from services.blindbox import generate_blindbox_route, normalize_theme


class TestBlindboxRoute(unittest.TestCase):
    def test_normalize_theme_supports_aliases(self):
        self.assertEqual(normalize_theme("吃吃喝喝"), "foodie")
        self.assertEqual(normalize_theme("文化之旅"), "culture")
        self.assertEqual(normalize_theme("未知主题"), "citywalk")

    def test_generate_citywalk_blindbox_route(self):
        result = generate_blindbox_route(preferences={
            "theme": "citywalk",
            "start_location": {"name": "湖滨银泰", "lng": 120.1646, "lat": 30.2552},
            "duration_hours": 4,
            "budget": 220,
            "transport": "walk"
        })

        self.assertTrue(result["success"])
        self.assertEqual(result["theme"], "citywalk")
        self.assertEqual(len(result["blind_boxes"]), 3)
        self.assertEqual(result["blind_box_info"]["theme"], "citywalk")
        self.assertIn("点击任意一个揭晓路线", result["blind_box_info"]["message"])

        for blind_box in result["blind_boxes"]:
            self.assertEqual(blind_box["display_name"], "神秘路线盲盒")
            self.assertFalse(blind_box["is_revealed"])
            self.assertNotIn("teaser", blind_box)
            self.assertNotIn("internal_strategy", blind_box)
            self.assertIn("option", blind_box)
            self.assertLessEqual(blind_box["option"]["total_cost"], 220)

    def test_generate_foodie_blindbox_route_prefers_food_pois(self):
        result = generate_blindbox_route(preferences={
            "theme": "吃吃喝喝",
            "start_location": {"name": "湖滨银泰", "lng": 120.1646, "lat": 30.2552},
            "duration_hours": 4,
            "budget": 260,
            "transport": "walk"
        })

        poi_types = {
            poi["type"]
            for blind_box in result["blind_boxes"]
            for poi in blind_box["option"]["pois"]
        }

        self.assertTrue(result["success"])
        self.assertEqual(result["theme"], "foodie")
        self.assertTrue(poi_types.intersection({"restaurant", "cafe", "drink", "dessert", "tea_house"}))

    def test_blind_boxes_do_not_expose_strategy_names(self):
        result = generate_blindbox_route(preferences={
            "theme": "citywalk",
            "start_location": {"name": "湖滨银泰", "lng": 120.1646, "lat": 30.2552},
            "duration_hours": 4,
            "budget": 260,
            "transport": "walk"
        })

        forbidden_words = ["稳妥", "小众", "主题直觉", "隐藏宝藏"]

        for blind_box in result["blind_boxes"]:
            visible_text = blind_box["display_name"]
            self.assertFalse(any(word in visible_text for word in forbidden_words))
            self.assertNotIn("box_name", blind_box)

    def test_blind_box_options_keep_route_details_and_have_different_pois(self):
        result = generate_blindbox_route(preferences={
            "theme": "citywalk",
            "start_location": {"name": "湖滨银泰", "lng": 120.1646, "lat": 30.2552},
            "duration_hours": 4,
            "budget": 260,
            "transport": "walk"
        })

        route_signatures = set()
        for blind_box in result["blind_boxes"]:
            option = blind_box["option"]
            for field in [
                "pois", "segments", "total_cost", "total_time", "total_wait_time",
                "summary", "explanation", "relaxation_notice", "differentiation_reason"
            ]:
                self.assertIn(field, option)
            route_signatures.add(tuple(poi["id"] for poi in option["pois"]))

        self.assertGreater(len(route_signatures), 1)

    def test_generate_blindbox_route_requires_start(self):
        result = generate_blindbox_route(preferences={
            "theme": "citywalk"
        })

        self.assertFalse(result["success"])
        self.assertIn("缺少盲盒路线起点坐标", result["message"])


if __name__ == "__main__":
    unittest.main()
