import unittest

from services.route_engine import generate_route_plan, normalize_route_request


class TestRouteEngine(unittest.TestCase):
    def test_frontend_request_format_still_generates_nested_route(self):
        result = generate_route_plan({
            "start": "120.1646,30.2552",
            "user_input": "周末想在杭州轻松逛逛",
            "preferences": {
                "city": "杭州",
                "food": ["杭帮菜"],
                "tags": ["本地风味", "放松"],
                "budget": 300,
                "time_window": ["10:00", "18:00"],
                "max_wait": 30,
                "duration_minutes": 240,
                "transport": "walk",
                "poi_count": 2
            }
        })

        self.assertTrue(result["success"])
        self.assertEqual(len(result["options"]), 3)
        first_success = next(option for option in result["options"] if option["success"])
        self.assertIn("type", first_success)
        self.assertIn("name", first_success)
        self.assertIn("route", first_success)
        self.assertGreaterEqual(len(first_success["route"]["pois"]), 1)

    def test_prd_request_format_is_normalized_to_engine_preferences(self):
        normalized = normalize_route_request({
            "mode": "standard",
            "start_location": {
                "name": "湖滨银泰",
                "lng": 120.1646,
                "lat": 30.2552
            },
            "duration_hours": 4,
            "budget": 200,
            "max_wait_time": 20,
            "preferences": ["川菜", "咖啡"],
            "companions": "friends",
            "transport": "walk"
        })

        self.assertEqual(normalized["start"]["name"], "湖滨银泰")
        self.assertEqual(normalized["preferences"]["duration_minutes"], 240)
        self.assertEqual(normalized["preferences"]["max_wait"], 20)
        self.assertEqual(normalized["preferences"]["food"], ["川菜", "咖啡"])
        self.assertEqual(normalized["preferences"]["tags"], ["川菜", "咖啡"])

    def test_prd_request_format_generates_prd_alias_fields(self):
        result = generate_route_plan({
            "mode": "standard",
            "start_location": {
                "name": "湖滨银泰",
                "lng": 120.1646,
                "lat": 30.2552
            },
            "duration_hours": 4,
            "budget": 200,
            "max_wait_time": 20,
            "preferences": ["川菜", "咖啡"],
            "companions": "friends",
            "transport": "walk"
        })

        self.assertTrue(result["success"])
        first_success = next(option for option in result["options"] if option["success"])
        self.assertEqual(first_success["plan_type"], first_success["type"])
        self.assertEqual(first_success["plan_name"], first_success["name"])
        self.assertEqual(first_success["total_cost"], first_success["route"]["total_cost"])
        self.assertEqual(first_success["pois"], first_success["route"]["pois"])
        self.assertEqual(first_success["segments"], first_success["route"]["segments"])
        self.assertEqual(first_success["explanation"], first_success["summary"])

if __name__ == '__main__':
    unittest.main()
