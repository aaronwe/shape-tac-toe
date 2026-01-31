import math

class Hex:
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
    def __init__(self, radius=6):
        self.radius = radius
        self.cells = {}
        self.bonuses = {}
        self._generate_board()

    def _generate_board(self):
        for q in range(-self.radius, self.radius + 1):
            for r in range(-self.radius, self.radius + 1):
                s = -q - r
                if abs(s) <= self.radius:
                    self.cells[Hex(q, r, s)] = None

    def get_content(self, hex_cell):
        return self.cells.get(hex_cell)

    def place_marker(self, hex_cell, marker):
        if hex_cell not in self.cells:
            return False
        if self.cells[hex_cell] is not None:
            return False
        self.cells[hex_cell] = marker
        return True

    def is_full(self):
        return all(content is not None for content in self.cells.values())
