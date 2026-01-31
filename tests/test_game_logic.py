
import unittest
import sys
import os

# Add parent directory to path so we can import game logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game import Game
from grid_logic import Hex

class TestGameLogic(unittest.TestCase):
    def test_random_start(self):
        """Verify that the starting player is randomized."""
        red_starts = 0
        blue_starts = 0
        for _ in range(100):
            g = Game(size=4)
            if g.current_player() == 'Red':
                red_starts += 1
            else:
                blue_starts += 1
        
        # It's statistically very unlikely to be 0 or 100 if random works
        print(f"Red starts: {red_starts}, Blue starts: {blue_starts}")
        self.assertTrue(red_starts > 20)
        self.assertTrue(blue_starts > 20)

    def test_first_move_restriction(self):
        """Verify that the first move must be at (0,0,0)."""
        g = Game(size=4)
        
        # Check valid moves
        valid = g.get_valid_moves()
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0], Hex(0, 0, 0))
        
        # Try invalid move
        success, msg = g.play_move(1, -1)
        self.assertFalse(success)
        self.assertIn("center", msg)
        
        # Try valid move
        success, msg = g.play_move(0, 0)
        self.assertTrue(success)
        
        # Second move: should allow neighbors
        valid_2 = g.get_valid_moves()
        self.assertTrue(len(valid_2) > 1) 
        self.assertNotIn(Hex(0, 0, 0), valid_2) # Center is taken

    def test_bonus_restriction(self):
        """Verify bonuses are only in outer 2 rings."""
        # Radius 6 board
        g = Game(size=6)
        bonuses = g.grid.bonuses.keys()
        
        for h in bonuses:
            dist = h.length()
            # Radius 6: outer rings are 6 and 5. So dist >= 5.
            self.assertTrue(dist >= 5, f"Bonus at {h} (dist {dist}) is not in outer 2 rings")

    def test_equal_turns(self):
        """Verify that the game ends on an even number of turns (equal turns)."""
        # Very small board to fill up quickly. Radius 2 = 1 + 6 + 12 = 19 hexes (Odd).
        # Should stop at 18 turns.
        g = Game(size=2, max_rounds=100)
        
        # Fill the board
        while not g.game_over:
            moves = g.get_valid_moves()
            if not moves:
                break
            m = moves[0]
            g.play_move(m.q, m.r)
            
        print(f"Game over at turn {g.turn_index}. Winner: {g.winner}")
        self.assertTrue(g.turn_index % 2 == 0)
        
        # Since 19 is odd, we expect 18 turns.
        self.assertEqual(g.turn_index, 18)

if __name__ == '__main__':
    unittest.main()
