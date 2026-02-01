from grid_logic import Hex

class Scorer:
    """
    Calculates the score for a given player on the board.
    
    This class contains the logic to identify geometric shapes (Lines, Loops, Triangles, etc.).
    It searches the grid for patterns formed by a player's markers.
    """
    def __init__(self, grid):
        self.grid = grid

    def calculate_score(self, player_marker, just_points=False):
        """
        Main function to compute the total score for a player.
        It calls individual helper methods for each shape type and sums up the points.
        Returns:
            ((total_score, all_shapes)) if just_points is False
            (total_score, []) if just_points is True (optimization)
        """
        total_score = 0
        all_shapes = []

        # 1. Score Lines
        if just_points:
             total_score += self._score_lines_fast(player_marker)
        else:
             s_lines, shapes_lines = self._score_lines(player_marker)
             total_score += s_lines
             all_shapes.extend(shapes_lines)

        # 2. Score Loops (Rings)
        if just_points:
             total_score += self._score_loops_fast(player_marker)
        else:
             s_loops, shapes_loops = self._score_loops(player_marker)
             total_score += s_loops
             all_shapes.extend(shapes_loops)

        # 3. Score Hollow Shapes (Diamonds/Parallelograms outlines)
        if just_points:
             total_score += self._score_hollow_shapes_fast(player_marker)
        else:
             s_hollow, shapes_hollow = self._score_hollow_shapes(player_marker)
             total_score += s_hollow
             all_shapes.extend(shapes_hollow)

        # 4. Score Triangles
        if just_points:
             total_score += self._score_triangles_fast(player_marker)
        else:
             s_tri, shapes_tri = self._score_triangles(player_marker)
             total_score += s_tri
             all_shapes.extend(shapes_tri)

        # 5. Variety Bonus
        # Incentivize shape diversity: Line + Triangle + Loop/Hollow = +30 pts
        # Note: Calculating variety bonus requires knowing WHICH shapes exist.
        # For 'just_points', we would effectively need to run the full detection logic or logic that returns bools.
        # To strictly optimize, we might skip this for AI heuristic or approximate it.
        # However, accurate scoring is better. 
        # For now, if just_points is True, we skip the Variety Bonus calculation to be purely fast
        # OR we implement fast detection boolean checks.
        # Let's keep it simple: The AI won't "know" about the Variety Bonus in the fast heuristic, 
        # which is a trade-off for speed. 
        # actually, let's just properly implement it in the slow path, and fast path ignores it for raw shape density.
        
        if not just_points:
            has_line = any(s['type'].startswith('line') for s in all_shapes)
            has_triangle = any(s['type'].startswith('triangle') for s in all_shapes)
            has_loop_or_hollow = any(s['type'] in ('loop', 'hollow_3x3', 'hollow_4x4') for s in all_shapes)
            
            if has_line and has_triangle and has_loop_or_hollow:
                bonus = 30
                total_score += bonus
                all_shapes.append({
                    'type': 'variety_bonus',
                    'points': bonus,
                    'cells': frozenset() 
                })

        return total_score, all_shapes

    # -------------------------------------------------------------------------
    # NON-OPTIMIZED METHODS (Return shapes list)
    # -------------------------------------------------------------------------
    def _score_lines(self, marker):
        """
        Finds straight lines of 3 or more markers.
        """
        score = 0
        shapes = []
        
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        directions = [Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1)]
        visited_in_direction = {d: set() for d in directions}

        for d in directions:
            for cell in player_cells:
                if cell in visited_in_direction[d]:
                    continue
                
                prev_cell = cell - d
                if prev_cell in player_cells:
                    continue 
                
                length = 0
                curr = cell
                line_cells = []
                
                while curr in player_cells:
                    length += 1
                    line_cells.append(curr)
                    visited_in_direction[d].add(curr)
                    curr = curr + d
                
                if length >= 3:
                     n = length - 2
                     base_pts = int(n * (n + 1) / 2)
                     pts = self._calculate_points(base_pts, line_cells)
                     score += pts
                     shapes.append({
                         'type': 'line',
                         'points': pts,
                         'cells': frozenset(line_cells) 
                     })
                     
        return score, shapes

    def _score_loops(self, marker):
        score = 0
        shapes = []
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        found_loops = set()
        
        directions = [
            Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1),
            Hex(-1, 1, 0), Hex(-1, 0, 1), Hex(0, -1, 1)
        ]

        for cell in player_cells:
            for d in directions:
                center = cell - d
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
                        base_pts = 15
                        pts = self._calculate_points(base_pts, loop_cells)
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
                            pts = self._calculate_points(points, path_vertices)
                            score += pts
                            shapes.append({
                                'type': f'hollow_{side_dots}x{side_dots}',
                                'points': pts,
                                'cells': shape_id
                            })
                        
        return score, shapes

    def _score_triangles(self, marker):
        score = 0
        shapes = []
        found_triangles = set()
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        
        neighbors = [
            Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1),
            Hex(-1, 1, 0), Hex(-1, 0, 1), Hex(0, -1, 1)
        ]
        
        for size in range(3, 9):
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
                            base_pts = size * 5
                            points = self._calculate_points(base_pts, triangle_pixels)
                            score += points
                            shapes.append({
                                'type': f'triangle_{size}',
                                'points': points,
                                'cells': t_id
                            })
                            
        return score, shapes

    # -------------------------------------------------------------------------
    # FAST METHODS (Return integer score only)
    # -------------------------------------------------------------------------
    def _score_lines_fast(self, marker):
        score = 0
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        directions = [Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1)]
        visited_in_direction = {d: set() for d in directions}

        for d in directions:
            for cell in player_cells:
                if cell in visited_in_direction[d]: continue
                if (cell - d) in player_cells: continue
                
                length = 0
                curr = cell
                # Just track points for multiplier
                line_cells = [] if self.has_bonuses else None
                
                while curr in player_cells:
                    length += 1
                    if self.has_bonuses: line_cells.append(curr)
                    visited_in_direction[d].add(curr)
                    curr = curr + d
                
                if length >= 3:
                     n = length - 2
                     base_pts = int(n * (n + 1) / 2)
                     if self.has_bonuses:
                         score += self._calculate_points(base_pts, line_cells)
                     else:
                         score += base_pts
        return score

    def _score_loops_fast(self, marker):
        score = 0
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        found_loops = set() # Store centers instead of full sets? No, need sets for uniquing overlapping
        # Actually, for loops, the center uniquely defines the loop for a player.
        # A player cannot have two loops with the same center.
        found_centers = set()
        
        directions = [
            Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1),
            Hex(-1, 1, 0), Hex(-1, 0, 1), Hex(0, -1, 1)
        ]

        for cell in player_cells:
            for d in directions:
                center = cell - d
                if center in found_centers: continue

                is_loop = True
                loop_points_list = [] if self.has_bonuses else None
                
                for neighbor_dir in directions:
                    neighbor = center + neighbor_dir
                    if neighbor not in player_cells:
                        is_loop = False
                        break
                    if self.has_bonuses: loop_points_list.append(neighbor)
                
                if is_loop:
                    found_centers.add(center)
                    base_pts = 15
                    if self.has_bonuses:
                        score += self._calculate_points(base_pts, loop_points_list)
                    else:
                        score += base_pts
        return score

    def _score_hollow_shapes_fast(self, marker):
        score = 0
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        orientations = [
             (Hex(1, -1, 0), Hex(0, 1, -1)),
             (Hex(0, 1, -1), Hex(-1, 1, 0)),
             (Hex(-1, 1, 0), Hex(-1, 0, 1))
        ]
        sizes = [(3, 4), (4, 8)]
        found_hollows = set() # Store frozenset of vertices to uniques

        for side_dots, points in sizes:
            steps = side_dots - 1
            for cell in player_cells:
                for u, v in orientations:
                    # We can identify a hollow shape uniquely by (start_cell, u, v).
                    # But verifying it requires checking the path.
                    current = cell
                    path_vertices = set()
                    path_vertices.add(cell)
                    valid = True

                    # Unroll loop for speed?
                    # 1. u
                    for _ in range(steps):
                        current = current + u
                        if current not in player_cells: valid = False; break
                        path_vertices.add(current)
                    if not valid: continue
                    
                    # 2. v
                    for _ in range(steps):
                        current = current + v
                        if current not in player_cells: valid = False; break
                        path_vertices.add(current)
                    if not valid: continue

                    # 3. -u
                    minus_u = Hex(0,0,0) - u
                    for _ in range(steps):
                        current = current + minus_u
                        if current not in player_cells: valid = False; break
                        path_vertices.add(current)
                    if not valid: continue

                    # 4. -v
                    minus_v = Hex(0,0,0) - v
                    for _ in range(steps):
                         current = current + minus_v
                         if current not in player_cells: valid = False; break
                         path_vertices.add(current)
                    if not valid: continue
                    
                    # If we got here, it's valid
                    shape_id = frozenset(path_vertices)
                    if shape_id not in found_hollows:
                        found_hollows.add(shape_id)
                        if self.has_bonuses:
                             score += self._calculate_points(points, path_vertices)
                        else:
                             score += points
        return score

    def _score_triangles_fast(self, marker):
        score = 0
        found_triangles_ids = set() # Identify by set of pixels
        player_cells = {h for h, m in self.grid.cells.items() if m == marker}
        
        neighbors = [
            Hex(1, -1, 0), Hex(1, 0, -1), Hex(0, 1, -1),
            Hex(-1, 1, 0), Hex(-1, 0, 1), Hex(0, -1, 1)
        ]
        
        for size in range(3, 9):
            for cell in player_cells:
                for i in range(6):
                    u = neighbors[i]
                    v = neighbors[(i+1)%6]
                    
                    triangle_pixels = set()
                    valid = True
                    for a in range(size):
                        for b in range(size - a):
                            p = Hex(cell.q + a*u.q + b*v.q, cell.r + a*u.r + b*v.r, cell.s + a*u.s + b*v.s)
                            if p not in player_cells:
                                valid = False
                                break
                            triangle_pixels.add(p)
                        if not valid: break
                    
                    if valid:
                        t_id = frozenset(triangle_pixels)
                        if t_id not in found_triangles_ids:
                            found_triangles_ids.add(t_id)
                            base_pts = size * 5
                            if self.has_bonuses:
                                score += self._calculate_points(base_pts, triangle_pixels)
                            else:
                                score += base_pts
        return score

    @property
    def has_bonuses(self):
        return hasattr(self.grid, 'bonuses') and self.grid.bonuses

    def _calculate_points(self, base_points, cells):
        """
        Applies bonus multipliers from the grid.
        """
        multiplier = 1
        if hasattr(self.grid, 'bonuses'):
            for cell in cells:
                multiplier *= self.grid.bonuses.get(cell, 1)
        return base_points * multiplier

    def _calculate_points(self, base_points, cells):
        """
        Applies bonus multipliers from the grid.
        If any cell in the shape is on a bonus tile, multiply the score.
        """
        multiplier = 1
        # Check if grid has bonuses attribute (handling case where it might not)
        if hasattr(self.grid, 'bonuses'):
            for cell in cells:
                multiplier *= self.grid.bonuses.get(cell, 1)
        return base_points * multiplier

