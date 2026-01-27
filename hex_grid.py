import math

class Hex:
    """
    Represents a single hexagon in a cube coordinate system (q, r, s).
    
    In a hexagonal grid, it's often easier to use 3 coordinates to represent position,
    similar to x, y, z in 3D space, but flattened onto a 2D plane.
    
    The pattern is:
    q: moves diagonal right-down
    r: moves straight down
    s: moves diagonal left-down (but is derived from q and r)
    
    Constraint: q + r + s must ALWAYS equal 0.
    This is the "Cube Coordinate" system property that makes the math work elegantly.
    
    Reference: https://www.redblobgames.com/grids/hexagons/
    """
    def __init__(self, q, r, s=None):
        self.q = q
        self.r = r
        # Calculate 's' automatically if it's not provided.
        # Since q + r + s = 0, we know that s = -q - r
        self.s = s if s is not None else (-q - r)
        
        # Verify the constraint is met (debugging check)
        assert self.q + self.r + self.s == 0, "q + r + s must be 0"

    def __eq__(self, other):
        # Override the equality operator (==) so we can compare two Hex objects
        # e.g., if Hex(1,0) == Hex(1,0)
        return self.q == other.q and self.r == other.r and self.s == other.s

    def __hash__(self):
        # Allow Hex objects to be used as keys in a dictionary (hash map) or items in a set.
        # Python needs a hash value to quickly look up objects.
        return hash((self.q, self.r, self.s))

    def __repr__(self):
        # String representation for debugging (e.g. when you print(hex))
        return f"Hex({self.q}, {self.r}, {self.s})"

    def __add__(self, other):
        # Add two vectors together. Example: moving from one hex to a neighbor.
        return Hex(self.q + other.q, self.r + other.r, self.s + other.s)

    def __sub__(self, other):
        # Subtract vectors. Useful for calculating distance or direction.
        return Hex(self.q - other.q, self.r - other.r, self.s - other.s)

    def length(self):
        # Calculate distance from center (0,0,0) logic.
        # In cube coordinates, distance is half the sum of absolute coordinates.
        return (abs(self.q) + abs(self.r) + abs(self.s)) // 2

    def distance(self, other):
        # Distance between two arbitrary hexes.
        # 1. Subtract one from the other to get the vector between them.
        # 2. Get the length of that vector.
        return (self - other).length()

    def neighbors(self):
        # Return a list of all 6 surrounding hexagons.
        # These are the "unit vectors" in a hex grid.
        vectors = [
            Hex(1, 0, -1), Hex(1, -1, 0), Hex(0, -1, 1),
            Hex(-1, 0, 1), Hex(-1, 1, 0), Hex(0, 1, -1)
        ]
        # List comprehension: create a new hex for each direction added to current position
        return [self + v for v in vectors]

class HexGrid:
    """
    Manages the board of hexagons.
    
    This class handles the storage of the game state (which cell has which marker).
    It generates a hexagonal-shaped map based on a "radius".
    """
    def __init__(self, radius=4):
        self.radius = radius
        # Dictionary to store the board state.
        # Key: Hex object (location)
        # Value: Content string ('Red', 'Blue', or None if empty)
        self.cells = {} 
        self._generate_board()

    def _generate_board(self):
        """
        Creates the keys for the self.cells dictionary.
        Logic: We iterate q from -radius to +radius.
        Then we iterate r, but r is constrained because we need to stay within the hex shape.
        """
        for q in range(-self.radius, self.radius + 1):
            # The range of r depends on q to maintain the hexagonal shape
            r1 = max(-self.radius, -q - self.radius)
            r2 = min(self.radius, -q + self.radius)
            for r in range(r1, r2 + 1):
                # Initialize every valid cell as Empty (None)
                self.cells[Hex(q, r)] = None

    def get_content(self, hex_cell):
        # Safely get what's at a specific coordinate
        return self.cells.get(hex_cell)

    def place_marker(self, hex_cell, marker):
        """
        Attempts to place a marker ('Red' or 'Blue') on the board.
        Returns True if successful, False if the move is invalid.
        """
        # Check if the coordinate actually exists on our board
        if hex_cell not in self.cells:
            return False # Invalid move: Off board
            
        # Check if the spot is already taken
        if self.cells[hex_cell] is not None:
            return False # Invalid move: Occupied
            
        # Valid move: Update the dictionary
        self.cells[hex_cell] = marker
        return True

    def is_full(self):
        # Check if every single cell in the dictionary has a value (is not None)
        # .values() gives us a list of all markers (or None)
        # `all(...)` returns True only if every item is truthy (not None/False)
        # Wait, None is falsy, so we check `content is not None` explicitly.
        return all(content is not None for content in self.cells.values())
