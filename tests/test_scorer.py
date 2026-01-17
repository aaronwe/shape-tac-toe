import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hex_grid import HexGrid, Hex
from scorer import Scorer

class TestScorer(unittest.TestCase):
    def setUp(self):
        self.grid = HexGrid(radius=4)
        self.scorer = Scorer(self.grid)

    def test_line_of_3(self):
        # Place a horizontal line of 3
        # (0,0), (1,-1), (2,-2)? No, (q,r,s)
        # Line neighbors: (0,0), (1,0) NO. Neighbors: (1,-1,0) (East)
        # Cell 1: (0,0)
        # Cell 2: (1,-1)
        # Cell 3: (2,-2)
        cells = [Hex(0,0), Hex(1,-1), Hex(2,-2)]
        for c in cells:
            self.grid.place_marker(c, 'X')
            
        score = self.scorer.calculate_score('X')
        # Expect 1 point (Line of 3) + 0 others
        # Check simple lines
        # Triangles? Size 2 triangle:
        # A(0,0), B(1,-1), C(0,-1)? -> (0,0) and (1,-1) are neighbors.
        # (0,-1) is neighbor of (0,0) (SE).
        # (1,-1) is neighbor of (0,-1) (NE of 0,-1 is +1,-1 -> 1,-2? No)
        # Let's check neighbors of (0,-1):
        # + (1, -1) -> (1, -2).
        # Wait.
        # Let's stick to lines.
        # These 3 cells are strictly linear. Check neighbors:
        # (0,0) -> (1,-1) [Vector 1,-1].
        # (1,-1) -> (2,-2) [Vector 1,-1].
        # It's a line.
        # Any triangle?
        # (0,0) and (2,-2) distance 2.
        # No triangles.
        self.assertEqual(score, 1, "Line of 3 should be 1 point")

    def test_line_of_4(self):
        cells = [Hex(0,0), Hex(1,-1), Hex(2,-2), Hex(3,-3)]
        for c in cells:
            self.grid.place_marker(c, 'X')
        score = self.scorer.calculate_score('X')
        # Line of 4: 1 + (4-3) = 2 points.
        self.assertEqual(score, 2)

    def test_rhombus_2x2(self):
        # 2x2 Rhombus (Parallelogram)
        # Defined by 3-4 cells.
        # Base (0,0). Side 1 (1,-1). Side 2 (0,1)?
        # (0,0), (1,-1,0), (0,1,-1), (1,0,-1)
        # Let's verify coordinates:
        # A(0,0,0)
        # B(1,-1,0) (East neighbor)
        # C(0,1,-1) (SE neighbor)
        # D(1,0,-1) (Common neighbor of B and C? 
        # B + SE = (1,-1) + (0,1) = (1,0). Yes.)
        cells = [Hex(0,0), Hex(1,-1), Hex(0,1), Hex(1,0)]
        for c in cells:
            self.grid.place_marker(c, 'X')
            
        # Shapes formed:
        # 1. Rhombus 2x2 (the whole thing). +2 pts.
        # 2. Triangles?
        # Triangle (A,B,D)? Side 2. (0,0), (1,-1), (1,0).
        # Dist(A,B)=1. Dist(A,D)=1. Dist(B,D)? (1,-1)-(1,0) = (0,-1). Len 1.
        # Yes, A,B,D is a triangle. +1 pt.
        # Triangle (A,C,D)? (0,0), (0,1), (1,0).
        # Dist(A,C)=1. Dist(A,D)=1. Dist(C,D) = (-1, 1). Len 1.
        # Yes, A,C,D is a triangle. +1 pt.
        # Total expected: 2 (Rhombus) + 1 (Triangle) + 1 (Triangle) = 4 points.
        # Any lines? No lines of length 3.
        
        score = self.scorer.calculate_score('X')
        self.assertEqual(score, 4)

if __name__ == '__main__':
    unittest.main()
