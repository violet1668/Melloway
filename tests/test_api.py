import unittest

from app import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_friends_center_api_returns_route(self):
        response = self.client.post("/api/friends/center", json={
            "friends_locations": [
                {"name": "A", "lng": 120.1600, "lat": 30.2600},
                {"name": "B", "lng": 120.1800, "lat": 30.2400}
            ],
            "budget": 260,
            "max_wait": 30,
            "duration_minutes": 240,
            "transport": "walk"
        })

        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("center", data)
        self.assertIn("route", data)
        self.assertGreaterEqual(len(data["pois"]), 1)

    def test_friends_center_api_rejects_single_location(self):
        response = self.client.post("/api/friends/center", json={
            "friends_locations": [
                {"name": "A", "lng": 120.1600, "lat": 30.2600}
            ]
        })

        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("至少提供 2 个朋友位置", data["message"])

    def test_blind_box_api_returns_route(self):
        response = self.client.post("/api/routes/blind-box", json={
            "theme": "citywalk",
            "start_location": {"name": "湖滨银泰", "lng": 120.1646, "lat": 30.2552},
            "duration_hours": 4,
            "budget": 220,
            "transport": "walk"
        })

        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["theme"], "citywalk")
        self.assertIn("blind_box_info", data)
        self.assertIn("blind_boxes", data)
        self.assertEqual(len(data["blind_boxes"]), 3)
        for blind_box in data["blind_boxes"]:
            self.assertEqual(blind_box["display_name"], "神秘路线盲盒")
            self.assertFalse(blind_box["is_revealed"])
            self.assertIn("option", blind_box)
            self.assertIn("pois", blind_box["option"])
            self.assertGreaterEqual(len(blind_box["option"]["pois"]), 1)

    def test_blind_box_api_rejects_missing_start(self):
        response = self.client.post("/api/routes/blind-box", json={
            "theme": "citywalk"
        })

        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("缺少盲盒路线起点坐标", data["message"])

if __name__ == '__main__':
    unittest.main()
