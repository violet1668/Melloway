import unittest

from services.friends import calculate_center_point, find_friends_route


class TestFriendsRoute(unittest.TestCase):
    def test_calculate_center_point_from_friend_locations(self):
        center = calculate_center_point([
            {"name": "A", "lng": 120.1600, "lat": 30.2600},
            {"name": "B", "lng": 120.1800, "lat": 30.2400}
        ])

        self.assertEqual(center["name"], "推荐集合点")
        self.assertEqual(center["source_count"], 2)
        self.assertAlmostEqual(center["lng"], 120.17)
        self.assertAlmostEqual(center["lat"], 30.25)

    def test_find_friends_route_generates_friend_friendly_route(self):
        result = find_friends_route(preferences={
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
        self.assertIn("center", result)
        self.assertGreaterEqual(len(result["pois"]), 1)
        self.assertIn("friend_fairness", result["pois"][0])
        self.assertLessEqual(result["total_time"], 240)

    def test_find_friends_route_requires_two_locations(self):
        with self.assertRaises(ValueError):
            find_friends_route(preferences={
                "friends_locations": [
                    {"name": "A", "lng": 120.1600, "lat": 30.2600}
                ]
            })


if __name__ == "__main__":
    unittest.main()
