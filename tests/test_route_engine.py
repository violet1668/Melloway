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

    def test_user_input_only_generates_routes_with_extracted_preferences(self):
        result = generate_route_plan({
            "start": "120.1646,30.2552",
            "user_input": "想找安静一点、适合拍照、能喝咖啡的citywalk路线"
        })

        insight = result["preference_insight"]

        self.assertTrue(result["success"])
        self.assertEqual(len(result["options"]), 3)
        self.assertIn("咖啡", insight["extracted_food"])
        self.assertIn("安静", insight["extracted_tags"])
        self.assertIn("适合拍照", insight["extracted_tags"])
        self.assertIn("citywalk", insight["extracted_tags"])
        self.assertEqual(insight["parser_source"], "rules")

    def test_user_input_extracts_budget_duration_wait_and_food(self):
        normalized = normalize_route_request({
            "start": "120.1646,30.2552",
            "user_input": "预算200，玩3小时，不想排队，想吃川菜再喝咖啡"
        })

        preferences = normalized["preferences"]
        insight = normalized["preference_insight"]

        self.assertEqual(preferences["budget"], 200)
        self.assertEqual(preferences["duration_minutes"], 180)
        self.assertEqual(preferences["max_wait"], 15)
        self.assertIn("川菜", preferences["food"])
        self.assertIn("咖啡", preferences["food"])
        self.assertEqual(insight["extracted_constraints"]["budget"], 200)
        self.assertEqual(insight["extracted_constraints"]["duration_minutes"], 180)
        self.assertEqual(insight["extracted_constraints"]["max_wait"], 15)

    def test_user_input_missing_constraints_returns_assumptions(self):
        result = generate_route_plan({
            "start": "120.1646,30.2552",
            "user_input": "想找安静一点、适合拍照、能喝咖啡的citywalk路线"
        })

        assumptions = result["preference_insight"]["assumptions"]

        self.assertTrue(assumptions["has_missing_constraints"])
        self.assertEqual(
            assumptions["missing_fields"],
            ["budget", "duration_minutes", "max_wait"]
        )
        self.assertIn("系统已默认", assumptions["message"])

    def test_explicit_constraints_are_not_overwritten_by_user_input(self):
        normalized = normalize_route_request({
            "start": "120.1646,30.2552",
            "user_input": "预算200，玩3小时，不想排队，想吃川菜再喝咖啡",
            "preferences": {
                "city": "杭州",
                "budget": 500,
                "duration_minutes": 360,
                "max_wait": 45,
                "food": ["杭帮菜"],
                "tags": ["本地风味"]
            }
        })

        preferences = normalized["preferences"]

        self.assertEqual(preferences["budget"], 500)
        self.assertEqual(preferences["duration_minutes"], 360)
        self.assertEqual(preferences["max_wait"], 45)
        self.assertEqual(preferences["food"], ["杭帮菜", "川菜", "咖啡"])

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

    def test_friends_mode_generates_three_options_from_center(self):
        result = generate_route_plan({
            "mode": "friends",
            "friends_locations": [
                {"name": "A", "lng": 120.1600, "lat": 30.2600},
                {"name": "B", "lng": 120.1800, "lat": 30.2400}
            ],
            "budget": 260,
            "max_wait": 30,
            "duration_minutes": 240,
            "transport": "walk"
        })

        self.assertTrue(result["success"])
        self.assertIn("friends_center", result)
        self.assertEqual(result["friends_center"]["name"], "推荐集合点")
        self.assertEqual(len(result["options"]), 3)

    def test_friends_mode_rejects_less_than_two_locations(self):
        result = generate_route_plan({
            "mode": "friends",
            "friends_locations": [
                {"name": "A", "lng": 120.1600, "lat": 30.2600}
            ]
        })

        self.assertFalse(result["success"])
        self.assertEqual(result["options"], [])
        self.assertIn("至少提供 2 个朋友位置", result["message"])

    def test_invalid_budget_returns_clear_message(self):
        result = generate_route_plan({
            "start": "120.1646,30.2552",
            "preferences": {
                "budget": -1
            }
        })

        self.assertFalse(result["success"])
        self.assertEqual(result["options"], [])
        self.assertIn("预算必须大于 0", result["message"])

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

    def test_route_generation_without_must_visit_pois_still_works(self):
        result = generate_route_plan(self._differentiation_request())

        self.assertTrue(result["success"])
        self.assertEqual(len(result["options"]), 3)
        for option in result["options"]:
            self.assertIn("must_visit_pois_included", option)
            self.assertIn("must_visit_pois_missing", option)
            self.assertEqual(option["must_visit_pois_included"], [])
            self.assertEqual(option["must_visit_pois_missing"], [])

    def test_existing_single_must_visit_poi_is_included(self):
        request_data = self._differentiation_request()
        request_data["must_visit_pois"] = ["poi_008"]

        result = generate_route_plan(request_data)

        self.assertTrue(result["success"])
        for option in result["options"]:
            route_poi_ids = [poi["id"] for poi in option["pois"]]
            included_ids = [poi["id"] for poi in option["must_visit_pois_included"]]
            self.assertIn("poi_008", route_poi_ids)
            self.assertIn("poi_008", included_ids)

    def test_two_existing_must_visit_pois_are_prioritized_by_demand_satisfaction(self):
        request_data = {
            "start": "120.1646,30.2552",
            "must_visit_pois": ["poi_010", {"id": "poi_008", "name": "西湖步行观景点"}],
            "preferences": {
                "city": "杭州",
                "food": ["杭帮菜"],
                "tags": ["本地风味", "放松"],
                "budget": 260,
                "time_window": ["10:00", "18:00"],
                "max_wait": 30,
                "duration_minutes": 260,
                "transport": "walk"
            }
        }

        result = generate_route_plan(request_data)
        demand_option = next(option for option in result["options"] if option["type"] == "demand_satisfaction")
        included_ids = {poi["id"] for poi in demand_option["must_visit_pois_included"]}

        self.assertTrue(demand_option["success"])
        self.assertEqual(included_ids, {"poi_010", "poi_008"})
        self.assertEqual(demand_option["must_visit_pois_missing"], [])

    def test_missing_must_visit_poi_id_returns_error(self):
        request_data = self._differentiation_request()
        request_data["must_visit_pois"] = ["poi_not_exists"]

        result = generate_route_plan(request_data)

        self.assertFalse(result["success"])
        self.assertEqual(result["options"], [])
        self.assertIn("未找到手动添加的 POI", result["message"])
        self.assertIn("poi_not_exists", result["message"])

    def test_hard_constraint_reports_missing_must_visit_pois_when_unavailable(self):
        request_data = {
            "start": "120.1646,30.2552",
            "must_visit_pois": ["poi_006"],
            "preferences": {
                "city": "杭州",
                "food": ["烤肉"],
                "tags": ["网红", "热闹"],
                "budget": 40,
                "time_window": ["10:00", "18:00"],
                "max_wait": 20,
                "duration_minutes": 120,
                "transport": "walk"
            }
        }

        result = generate_route_plan(request_data)
        hard_option = next(option for option in result["options"] if option["type"] == "hard_constraint")
        missing_ids = [poi["id"] for poi in hard_option["must_visit_pois_missing"]]

        self.assertTrue(hard_option["success"])
        self.assertIn("poi_006", missing_ids)
        self.assertIn("未纳入", hard_option["differentiation_reason"])
        self.assertNotIn("poi_006", [poi["id"] for poi in hard_option["pois"]])

if __name__ == '__main__':
    unittest.main()
