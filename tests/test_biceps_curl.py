import unittest
import math
from detectors.biceps_curl import BicepsCurlDetector

class TestBicepsCurlDetector(unittest.TestCase):
    def setUp(self):
        self.detector = BicepsCurlDetector()

    def test_safe_angle_normal(self):
        # 45 degree angle: dx=1, dy=1
        result = self.detector._safe_angle(1, 1)
        self.assertAlmostEqual(result, 45.0)

    def test_safe_angle_dy_zero(self):
        # dy=0 should return 0.0
        result = self.detector._safe_angle(1, 0)
        self.assertEqual(result, 0.0)

        result = self.detector._safe_angle(-1, 0)
        self.assertEqual(result, 0.0)

        result = self.detector._safe_angle(0, 0)
        self.assertEqual(result, 0.0)

    def test_safe_angle_dx_zero(self):
        # dx=0, dy!=0
        result = self.detector._safe_angle(0, 1)
        self.assertEqual(result, 0.0)

    def test_safe_angle_negative_values(self):
        # The method uses abs(dx) and abs(dy), so results should be positive
        result1 = self.detector._safe_angle(-1, 1)
        self.assertAlmostEqual(result1, 45.0)

        result2 = self.detector._safe_angle(1, -1)
        self.assertAlmostEqual(result2, 45.0)

        result3 = self.detector._safe_angle(-1, -1)
        self.assertAlmostEqual(result3, 45.0)

if __name__ == '__main__':
    unittest.main()
