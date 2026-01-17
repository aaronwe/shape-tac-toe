from hex_grid import Hex

class Scorer:
    """
    Calculates the score for a given player on the board.
    """
    def __init__(self, grid):
        self.grid = grid

    def calculate_score(self, player_marker):
        total_score = 0
        all_shapes = []

        s_lines, shapes_lines = self._score_lines(player_marker)
        total_score += s_lines
        all_shapes.extend(shapes_lines)

        # Rhombus removed

        s_loops, shapes_loops = self._score_loops(player_marker)
        total_score += s_loops
        all_shapes.extend(shapes_loops)

        s_hollow, shapes_hollow = self._score_hollow_shapes(player_marker)
        total_score += s_hollow
        all_shapes.extend(shapes_hollow)

        s_tri, shapes_tri = self._score_triangles(player_marker)
        total_score += s_tri
        all_shapes.extend(shapes_tri)

        return total_score, all_shapes

    def _score_lines(self, marker):
        score = 0
        shapes = []
        
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        directions = [Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1)]
        
        visited_in_direction = {d: set() for d in directions}

        for d in directions:
            for cell in player_cells:
                if cell in visited_in_direction[d]:
                    continue
                
                # Check if this is the start of a segment (previous cell empty or different marker)
                prev_cell = cell - d
                if prev_cell in player_cells:
                    continue
                
                # Trace line
                length = 0
                curr = cell
                line_cells = []
                while curr in player_cells:
                    length += 1
                    line_cells.append(curr)
                    visited_in_direction[d].add(curr)
                    curr = curr + d
                
                if length >= 3:
                     pts = 1 + (length - 3)
                     score += pts
                     shapes.append({
                         'type': 'line',
                         'points': pts,
                         'cells': frozenset(line_cells)
                     })
                     
        return score, shapes

    def _score_loops(self, marker):
        # A Loop is 6 hexes in a circle around a center.
        # Start with any player cell, assume it's part of a loop.
        # It must be a neighbor of the center.
        score = 0
        shapes = []
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        found_loops = set()
        
        # Directions for neighbors
        directions = [
            Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1),
            Hex(-1, 1, 0), Hex(-1, 0, 1), Hex(0, -1, 1)
        ]

        for cell in player_cells:
            # Check all 6 directions as possible centers relative to 'cell'
            # If 'cell' is neighbor of 'center', then 'center' = 'cell' + 'dir'? 
            # No, 'cell' = 'center' + 'dir'. So 'center' = 'cell' - 'dir'.
            for d in directions:
                center = cell - d
                
                # Check if this center forms a loop with current player's pieces
                loop_cells = set()
                is_loop = True
                for neighbor_dir in directions:
                    neighbor = center + neighbor_dir
                    if neighbor not in player_cells:
                        is_loop = False
                        break
                    loop_cells.add(neighbor)
                
                if is_loop:
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
        score = 0
        shapes = []
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        
        orientations = [
             (Hex(1, -1, 0), Hex(0, 1, -1)),
             (Hex(0, 1, -1), Hex(-1, 1, 0)),
             (Hex(-1, 1, 0), Hex(-1, 0, 1))
        ]
        
        # (Side Length in dots, Points)
        # Size 3 = Hollow 3x3 -> 4 points
        # Size 4 = Hollow 4x4 -> 8 points
        # Note: Size 2 (Loop) is handled separately now as it is a hexagon, not rhombus logic.
        sizes = [(3, 4), (4, 8)]
        
        found_hollows = set()

        for side_dots, points in sizes:
            steps = side_dots - 1
            for cell in player_cells:
                for u, v in orientations:
                    path_vertices = set()
                    path_vertices.add(cell)
                    current = cell
                    
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
        score = 0
        shapes = []
        found_triangles = set() # Set of frozenset(coords)
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        
        neighbors = [
            Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1),
            Hex(-1, 1, 0), Hex(-1, 0, 1), Hex(0, -1, 1)
        ]
        
        # Iterate sizes: 2 to 8
        for size in range(2, 9):
            for cell in player_cells:
                for i in range(6):
                    u = neighbors[i]
                    v = neighbors[(i+1)%6]
                    
                    triangle_pixels = set()
                    valid = True
                    for a in range(size):
                        for b in range(size - a):
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
