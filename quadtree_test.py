import unittest
from collections import namedtuple
import random
from local.quadtree import QuadtreePegs, Rectangle

# Import the quadtree module to test its functionality

# Define a simple Vector and FakePeg for testing purposes
Vector = namedtuple("Vector", ["x", "y"])

class FakePeg:
    def __init__(self, x, y):
        self.pos = Vector(x, y)

class TestQuadtreePegs(unittest.TestCase):
    def setUp(self):
        # Create a boundary that covers a 200x200 area centered at (100,100)
        self.boundary = Rectangle(100, 100, 100, 100)
        # Use a capacity that forces subdivisions quickly for testing
        self.qt = QuadtreePegs(self.boundary, numPegs=16)

    def test_insert_inside(self):
        # Insert a peg well within the boundary
        peg = FakePeg(100, 100)
        inserted = self.qt.insert(peg)
        self.assertTrue(inserted)
        self.assertIn(peg, self.qt.pegs)

    def test_insert_outside(self):
        # Create a peg outside the boundary
        peg = FakePeg(250, 250)
        inserted = self.qt.insert(peg)
        self.assertFalse(inserted)

    def test_subdivide_and_insert(self):
        # Insert enough pegs to force subdivision
        pegs = [FakePeg(100 + random.uniform(-50, 50), 
                         100 + random.uniform(-50, 50)) for _ in range(20)]
        count = 0
        for peg in pegs:
            if self.qt.insert(peg):
                count += 1
        self.assertEqual(count, len(pegs))
        # Check that quadtree is subdivided after exceeding capacity
        self.assertTrue(self.qt.divided)

    def test_query(self):
        # Insert multiple pegs in known positions
        pegs = [
            FakePeg(90, 90),
            FakePeg(110, 90),
            FakePeg(90, 110),
            FakePeg(110, 110),
            FakePeg(150, 150)  # Outside query
        ]
        for peg in pegs:
            self.qt.insert(peg)

        # Query a rectangle that should catch the first four pegs
        query_range = Rectangle(100, 100, 20, 20)
        found = self.qt.query(query_range)
        self.assertEqual(len(found), 4)
        for peg in found:
            self.assertTrue(query_range.contains(peg))

if __name__ == "__main__":
    unittest.main()