from hex_grid import Hex

class Scorer:
    """
    Calculates the score for a given player on the board.
    
    This class contains the logic to identify geometric shapes (Lines, Loops, Triangles, etc.).
    It searches the grid for patterns formed by a player's markers.
    """
    def __init__(self, grid):
        self.grid = grid

    def calculate_score(self, player_marker):
        """
        Main function to compute the total score for a player.
        It calls individual helper methods for each shape type and sums up the points.
        Returns:
            total_score (int): Total points.
            all_shapes (list): List of dictionaries describing every shape found (for UI highlighting).
        """
        total_score = 0
        all_shapes = []

        # 1. Score Lines
        s_lines, shapes_lines = self._score_lines(player_marker)
        total_score += s_lines
        all_shapes.extend(shapes_lines)

        # 2. Score Loops (Rings)
        s_loops, shapes_loops = self._score_loops(player_marker)
        total_score += s_loops
        all_shapes.extend(shapes_loops)

        # 3. Score Hollow Shapes (Diamonds/Parallelograms outlines)
        s_hollow, shapes_hollow = self._score_hollow_shapes(player_marker)
        total_score += s_hollow
        all_shapes.extend(shapes_hollow)

        # 4. Score Triangles
        s_tri, shapes_tri = self._score_triangles(player_marker)
        total_score += s_tri
        all_shapes.extend(shapes_tri)

        return total_score, all_shapes

    def _score_lines(self, marker):
        """
        Finds straight lines of 3 or more markers.
        """
        score = 0
        shapes = []
        
        # Get all cells occupied by the current player
        # This is a set comprehension (like list comprehension but creates a set)
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        
        # We only need to check 3 directions (axes). 
        # Checking the opposite directions (e.g., Left vs Right) would just find the same line twice.
        directions = [Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1)]
        
        # Keep track of visited cells per direction to avoid double counting segments
        visited_in_direction = {d: set() for d in directions}

        for d in directions:
            for cell in player_cells:
                # If we already counted this cell in this direction, skip it
                if cell in visited_in_direction[d]:
                    continue
                
                # Check if this cell is the START of a line.
                # It determines this by seeing if the cell *behind* it (cell - d) is empty or different.
                prev_cell = cell - d
                if prev_cell in player_cells:
                    continue # Not the start, so skip (we will catch it when we process the start node)
                
                # Trace the line forward
                length = 0
                curr = cell
                line_cells = []
                
                # Keep moving in direction 'd' as long as we see our own marker
                while curr in player_cells:
                    length += 1
                    line_cells.append(curr)
                    visited_in_direction[d].add(curr) # Mark as visited so we don't re-process
                    curr = curr + d
                
                # If the line is long enough (3+), add points
                if length >= 3:
                     # Formula: 1 point for the first 3, plus 1 point for each extra
                     pts = 1 + (length - 3)
                     score += pts
                     shapes.append({
                         'type': 'line',
                         'points': pts,
                         'cells': frozenset(line_cells) # frozenset is an immutable set (can be hashed)
                     })
                     
        return score, shapes

    def _score_loops(self, marker):
        """
        Finds "Loops" or "Rings" (6 markers surrounding a center).
        """
        score = 0
        shapes = []
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        found_loops = set()
        
        # The 6 vectors to neighbor cells
        directions = [
            Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1),
            Hex(-1, 1, 0), Hex(-1, 0, 1), Hex(0, -1, 1)
        ]

        # Algorithm:
        # Instead of looking for a pattern, we assume every empty spot could be a "center".
        # But iterating all empty spots is one way.
        # Here, we iterate player cells and check "If I am part of a loop, where would the center be?"
        for cell in player_cells:
            # A cell can be a neighbor to a center in 6 different directions.
            for d in directions:
                # Mathematically, if 'cell' is neighbor to 'center', 
                # then 'center' is 'cell' moved in the opposite direction.
                # Or simply: 'center' is in direction -d from 'cell'.
                # Let's check a potential center.
                center = cell - d
                
                # Check if this center is surrounded by 6 of our markers
                loop_cells = set()
                is_loop = True
                for neighbor_dir in directions:
                    neighbor = center + neighbor_dir
                    if neighbor not in player_cells:
                        is_loop = False
                        break
                    loop_cells.add(neighbor)
                
                if is_loop:
                    # We found a loop! Use a frozenset to uniquely identify it 
                    # (so we don't count the same loop 6 times, once for each component cell)
                    loop_id = frozenset(loop_cells)
                    if loop_id not in found_loops:
                        found_loops.add(loop_id)
                        pts = 6
                        score += pts
                        shapes.append({
                            'type': 'loop',
                            'points': pts,
                            'cells': loop_id
                        })
                        
        return score, shapes

    def _score_hollow_shapes(self, marker):
        """
        Finds "Hollow Shapes" (outlines of shapes like 3x3 or 4x4 diamonds).
        This detects if a player has drawn the border of a larger shape.
        """
        score = 0
        shapes = []
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        
        # Hexagonal grid axes pairs that define "rhombus/diamond" shapes
        orientations = [
             (Hex(1, -1, 0), Hex(0, 1, -1)),  # Axis pair 1
             (Hex(0, 1, -1), Hex(-1, 1, 0)),  # Axis pair 2
             (Hex(-1, 1, 0), Hex(-1, 0, 1))   # Axis pair 3
        ]
        
        # Config: (Side Length in dots, Points)
        # Size 3 = Hollow 3x3 (requires 8 dots to draw outline) -> 4 points
        # Size 4 = Hollow 4x4 (requires 12 dots) -> 8 points
        sizes = [(3, 4), (4, 8)]
        
        found_hollows = set()

        for side_dots, points in sizes:
            steps = side_dots - 1
            for cell in player_cells:
                # Try to trace a shape starting from 'cell' in each orientation
                for u, v in orientations:
                    path_vertices = set()
                    path_vertices.add(cell)
                    current = cell
                    
                    # Trace key:
                    # 1. Move 'steps' times in direction u
                    # 2. Move 'steps' times in direction v
                    # 3. Move 'steps' times in direction -u (backwards u)
                    # 4. Move 'steps' times in direction -v (backwards v)
                    # If we make it back to start and all are filled, it's a shape.
                    
                    # 1. u
                    for _ in range(steps):
                        current = current + u
                        path_vertices.add(current)
                    # 2. v
                    for _ in range(steps):
                        current = current + v
                        path_vertices.add(current)
                    # 3. -u
                    minus_u = Hex(0,0,0) - u
                    for _ in range(steps):
                        current = current + minus_u
                        path_vertices.add(current)
                    # 4. -v
                    minus_v = Hex(0,0,0) - v
                    for _ in range(steps):
                         current = current + minus_v
                         path_vertices.add(current)
                         
                    # Check if all vertices in this path belong to the player
                    if path_vertices.issubset(player_cells):
                        shape_id = frozenset(path_vertices)
                        if shape_id not in found_hollows:
                            found_hollows.add(shape_id)
                            score += points
                            
                            shapes.append({
                                'type': f'hollow_{side_dots}x{side_dots}',
                                'points': points,
                                'cells': shape_id
                            })
                        
        return score, shapes

    def _score_triangles(self, marker):
        """
        Finds FILLED triangles of various sizes.
        Size 2 triangle = 3 dots (pyramid).
        Size 3 triangle = 6 dots.
        """
        score = 0
        shapes = []
        found_triangles = set() # Set of frozenset(coords) to avoid duplicates
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        
        neighbors = [
            Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1),
            Hex(-1, 1, 0), Hex(-1, 0, 1), Hex(0, -1, 1)
        ]
        
        # Iterate sizes: 2 "dots wide" up to 8
        for size in range(2, 9):
            for cell in player_cells:
                # A triangle is defined by 2 direction vectors (edges from a vertex)
                for i in range(6):
                    u = neighbors[i]
                    v = neighbors[(i+1)%6] # Next neighbor in sequence
                    
                    triangle_pixels = set()
                    valid = True
                    
                    # Iterate through the grid points inside the triangle defined by u and v
                    # 'a' and 'b' are coordinates in the local basis (u, v)
                    for a in range(size):
                        for b in range(size - a):
                            # Map local (a, b) back to global Hex coordinates
                            p = Hex(
                                cell.q + a*u.q + b*v.q,
                                cell.r + a*u.r + b*v.r,
                                cell.s + a*u.s + b*v.s
                            )
                            if p not in player_cells:
                                valid = False
                                break
                            triangle_pixels.add(p)
                        if not valid:
                            break
                    
                    if valid:
                        t_id = frozenset(triangle_pixels)
                        if t_id not in found_triangles:
                            found_triangles.add(t_id)
                            points = 1 if size == 2 else size
                            score += points
                            shapes.append({
                                'type': f'triangle_{size}',
                                'points': points,
                                'cells': t_id
                            })
                            
        return score, shapes
