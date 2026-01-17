import math

class Hex:
    """
    Represents a single hexagon in a cube coordinate system (q, r, s).
    Constraint: q + r + s = 0
    Reference: https://www.redblobgames.com/grids/hexagons/
    """
    def __init__(self, q, r, s=None):
        self.q = q
        self.r = r
        self.s = s if s is not None else (-q - r)
        assert self.q + self.r + self.s == 0, "q + r + s must be 0"

    def __eq__(self, other):
        return self.q == other.q and self.r == other.r and self.s == other.s

    def __hash__(self):
        return hash((self.q, self.r, self.s))

    def __repr__(self):
        return f"Hex({self.q}, {self.r}, {self.s})"

    def __add__(self, other):
        return Hex(self.q + other.q, self.r + other.r, self.s + other.s)

    def __sub__(self, other):
        return Hex(self.q - other.q, self.r - other.r, self.s - other.s)

    def length(self):
        return (abs(self.q) + abs(self.r) + abs(self.s)) // 2

    def distance(self, other):
        return (self - other).length()

    def neighbors(self):
        vectors = [
            Hex(1, 0, -1), Hex(1, -1, 0), Hex(0, -1, 1),
            Hex(-1, 0, 1), Hex(-1, 1, 0), Hex(0, 1, -1)
        ]
        return [self + v for v in vectors]

class HexGrid:
    """
    Manages the board of hexagons.
    We'll use a "pointy topped" orientation, but the math is mostly orientation agnostic.
    The board is "at least 8x8". A hexagonal grid with a radius of N handles this well.
    Alternatively, we can define a rectangular shape in hex coordinates (doubled coordinates or axial).
    Let's stick to a simple radius-based map or a parallelogram map for simplicity.
    To match "8x8" rectangular thinking, a radius of 4 or 5 is roughly appropriate.
    Let's go with a map radius of 4 (generates a substantial hex shaped board).
    Radius 4 = 1 + 6*1 + ... it's a hexagon shape.
    User asked for "grid of at least 8x8".
    Let's just store the hexes in a dictionary.
    """
    def __init__(self, radius=4):
        self.radius = radius
        self.cells = {} # Map Hex -> Content (None, 'X', 'O')
        self._generate_board()

    def _generate_board(self):
        # Generate a hexagonal shaped board
        for q in range(-self.radius, self.radius + 1):
            r1 = max(-self.radius, -q - self.radius)
            r2 = min(self.radius, -q + self.radius)
            for r in range(r1, r2 + 1):
                self.cells[Hex(q, r)] = None

    def get_content(self, hex_cell):
        return self.cells.get(hex_cell)

    def place_marker(self, hex_cell, marker):
        """
        Returns True if placed successfully, False if multiple or invalid.
        """
        if hex_cell not in self.cells:
            return False # Off board
        if self.cells[hex_cell] is not None:
            return False # Occupied
        self.cells[hex_cell] = marker
        return True

    def is_full(self):
        return all(content is not None for content in self.cells.values())
