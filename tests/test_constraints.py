import unittest

from services.constraints import estimate_travel_minutes


class TestConstraints(unittest.TestCase):
    def test_estimate_travel_minutes_applies_detour_factor(self):
        self.assertEqual(estimate_travel_minutes(10, "walk"), 153)
        self.assertEqual(estimate_travel_minutes(10, "bike"), 62)
        self.assertEqual(estimate_travel_minutes(10, "drive"), 32)

    def test_estimate_travel_minutes_applies_peak_factor(self):
        self.assertEqual(estimate_travel_minutes(10, "drive", depart_time="08:00"), 45)
        self.assertEqual(estimate_travel_minutes(10, "drive", depart_time="18:00"), 48)
        self.assertEqual(estimate_travel_minutes(10, "bike", depart_time="08:00"), 68)
        self.assertEqual(estimate_travel_minutes(10, "walk", depart_time="08:00"), 153)

    def test_estimate_travel_minutes_ignores_invalid_depart_time(self):
        self.assertEqual(estimate_travel_minutes(10, "drive", depart_time="bad-time"), 32)

if __name__ == '__main__':
    unittest.main()
