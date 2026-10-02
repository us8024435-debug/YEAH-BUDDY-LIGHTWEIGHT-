import unittest
import math
from core.base_exercise import BaseExercise

class DummyExercise(BaseExercise):
    def process(self, landmarks):
        pass

    def reset(self):
        pass

class TestBaseExercise(unittest.TestCase):
    def setUp(self):
        self.exercise = DummyExercise()

    def test_calculate_angle_90_degrees(self):
        # A right triangle at origin
        a = (0, 1)
        b = (0, 0)
        c = (1, 0)
        angle = self.exercise.calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 90.0, places=5)

    def test_calculate_angle_180_degrees(self):
        # Collinear points in opposite directions
        a = (-1, 0)
        b = (0, 0)
        c = (1, 0)
        angle = self.exercise.calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 180.0, places=5)

    def test_calculate_angle_0_degrees(self):
        # Collinear points in the same direction
        a = (1, 0)
        b = (0, 0)
        c = (2, 0)
        angle = self.exercise.calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 0.0, places=5)

    def test_calculate_angle_identical_points(self):
        # Identical points -> magnitude is 0, returning 0.0
        a = (0, 0)
        b = (0, 0)
        c = (0, 0)
        angle = self.exercise.calculate_angle(a, b, c)
        self.assertEqual(angle, 0.0)

    def test_calculate_angle_one_identical_point(self):
        # One point identical to center point -> magnitude is 0, returning 0.0
        a = (0, 0)
        b = (0, 0)
        c = (1, 0)
        angle = self.exercise.calculate_angle(a, b, c)
        self.assertEqual(angle, 0.0)

        # Other point identical to center point
        a = (1, 0)
        b = (0, 0)
        c = (0, 0)
        angle = self.exercise.calculate_angle(a, b, c)
        self.assertEqual(angle, 0.0)

    def test_get_point(self):
        class DummyPoint:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        landmarks = [DummyPoint(1.0, 2.0), DummyPoint(3.0, 4.0)]
        point = self.exercise.get_point(landmarks, 1)
        self.assertEqual(point, (3.0, 4.0))

    def test_process(self):
        self.assertIsNone(self.exercise.process([]))

    def test_reset(self):
        self.assertIsNone(self.exercise.reset())

if __name__ == '__main__':
    unittest.main()
