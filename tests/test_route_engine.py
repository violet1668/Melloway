import unittest

from services.route_engine import generate_route_plan, normalize_route_request


class TestRouteEngine(unittest.TestCase):
    def _differentiation_request(self):
        return {
            "start": "120.1646,30.2552",
            "user_input": "周末想吃杭帮菜和咖啡，轻松逛逛",
            "preferences": {
                "city": "杭州",
                "food": ["杭帮菜", "咖啡"],
                "tags": ["本地风味", "放松", "适合聊天"],
                "budget": 180,
                "time_window": ["10:00", "18:00"],
                "max_wait": 20,
                "duration_minutes": 210,
                "transport": "walk"
            }
        }

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

    def test_options_use_different_route_selection_strategies(self):
        result = generate_route_plan(self._differentiation_request())

        successful_options = [option for option in result["options"] if option["success"]]
        route_signatures = {
            tuple(poi["id"] for poi in option["pois"])
            for option in successful_options
        }

        self.assertEqual(len(successful_options), 3)
        self.assertEqual(len(result["options"]), 3)
        self.assertGreater(len(route_signatures), 1)

    def test_options_include_constraint_explanation_fields(self):
        result = generate_route_plan(self._differentiation_request())

        for option in result["options"]:
            self.assertIn("constraint_policy", option)
            self.assertIn("relaxed_constraints", option)
            self.assertIn("relaxation_notice", option)
            self.assertIn("differentiation_reason", option)
            self.assertTrue(option["relaxation_notice"])
            self.assertTrue(option["differentiation_reason"])

    def test_hard_constraint_route_keeps_total_cost_within_budget(self):
        request_data = self._differentiation_request()
        preferences = request_data["preferences"]
        result = generate_route_plan(request_data)

        hard_option = next(option for option in result["options"] if option["type"] == "hard_constraint")

        self.assertTrue(hard_option["success"])
        self.assertLessEqual(hard_option["total_cost"], preferences["budget"])
        self.assertLessEqual(hard_option["total_time"], preferences["duration_minutes"])
        self.assertTrue(all(poi["wait_time"] <= preferences["max_wait"] for poi in hard_option["pois"]))
        self.assertFalse(hard_option["constraint_policy"]["allows_relaxation"])
        self.assertEqual(
            hard_option["relaxation_notice"],
            "该方案严格遵守你的预算、排队和时间限制。"
        )

    def test_preference_insight_prioritizes_hidden_gems_when_available(self):
        result = generate_route_plan({
            "start": "120.1646,30.2552",
            "user_input": "想找安静小众适合聊天的地方",
            "preferences": {
                "city": "杭州",
                "food": ["咖啡", "茶饮"],
                "tags": ["安静", "小众", "适合聊天"],
                "budget": 220,
                "time_window": ["10:00", "18:00"],
                "max_wait": 25,
                "duration_minutes": 240,
                "transport": "walk"
            }
        })

        insight_option = next(option for option in result["options"] if option["type"] == "preference_insight")

        self.assertTrue(insight_option["success"])
        self.assertTrue(any(poi["is_hidden_gem"] for poi in insight_option["pois"]))

    def test_relaxed_options_report_notice_when_relaxation_is_used(self):
        result = generate_route_plan(self._differentiation_request())

        for option_type in ["demand_satisfaction", "preference_insight"]:
            option = next(option for option in result["options"] if option["type"] == option_type)
            relaxed = option["relaxed_constraints"]
            uses_relaxation = (
                option["total_cost"] > relaxed["original_budget"]
                or option["total_time"] > relaxed["original_duration_minutes"]
                or any(poi["wait_time"] > relaxed["original_max_wait"] for poi in option["pois"])
            )

            if uses_relaxation:
                self.assertIn("为了更好满足你的偏好", option["relaxation_notice"])

if __name__ == '__main__':
    unittest.main()
