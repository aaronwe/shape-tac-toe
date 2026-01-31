from grid_logic import HexGrid, Hex
from scorer import Scorer


class Game:
    """
    The main Controller for the Shape Tac Toe game.
    
    This class manages:
    1. The Game Loop (whose turn is it?)
    2. The Board State (placed markers)
    3. The Scores (calculating and updating)
    4. The Win Conditions
    """
    def __init__(self, size=4, max_rounds=25, player_agents=None):
        # Initialize the hexagonal grid
        self.grid = HexGrid(radius=size)
        # Initialize the scorer with our grid
        self.scorer = Scorer(self.grid)
        
        # Player configuration
        self.players = ['Red', 'Blue']
        # Default agents: None means Human (or external controller)
        self.agents = player_agents if player_agents else {'Red': None, 'Blue': None}
        
        self.turn_index = 0
        self.scores = {'Red': 0, 'Blue': 0}
        
        # Randomize start player
        import random
        random.shuffle(self.players)
        
        # Generate Bonus Tiles (5 random tiles get 2x multiplier)
        # RESTRICTION: Bonus tiles only in outer 2 rings
        # Radius 6 board. Outer rings are radius 6 and 5.
        # Generally: dist >= radius - 1
        all_hexes = list(self.grid.cells.keys())
        radius = self.grid.radius
        outer_hexes = [h for h in all_hexes if h.length() >= radius - 1]
        
        if len(outer_hexes) > 5:
            bonus_hexes = random.sample(outer_hexes, 5) 
            for h in bonus_hexes:
                self.grid.bonuses[h] = 2
        elif len(all_hexes) > 5:
            # Fallback if board is tiny (radius < 2)
            bonus_hexes = random.sample(all_hexes, 5)
            for h in bonus_hexes:
                self.grid.bonuses[h] = 2
        
        # Game status flags
        self.winner = None
        self.game_over = False
        self.log = [] # A list of string messages for the UI
        self.max_rounds = max_rounds # Rounds per player
        
        # Tracking "New" Shapes:
        # We need to remember which shapes we've already scored so we don't
        # score the same Triangle twice every turn.
        self.existing_shapes = {'Red': set(), 'Blue': set()}
        
        # Temporary state for the UI (to show animations)
        self.last_scoring_event = [] # List of new shapes from the last move
        self.last_turn_points = {'Red': 0, 'Blue': 0} # Points scored in the most recent turn for each player
        self.last_turn_shapes = {'Red': [], 'Blue': []} # Shapes scored in the most recent turn for each player 

    def current_player(self):
        # Returns 'Red' or 'Blue' based on the turn index.
        # Returns 'Red' or 'Blue' based on the turn index.
        # self.players is shuffled at start, so 0 is the start player.
        return self.players[self.turn_index % 2]
    
    def get_valid_moves(self):
        """
        Returns a list of Hex cells where a move is currently legal.
        Rule: Must be within distance 2 of an existing tile (Loose Adjacency).
        """
        occupied = [h for h, m in self.grid.cells.items() if m is not None]
        
        # If board is empty, force first move to center
        # Or rather, turn_index == 0
        if self.turn_index == 0:
            center = Hex(0, 0, 0)
            if center in self.grid.cells and self.grid.cells[center] is None:
                return [center]
        
        # If board is otherwise empty (shouldn't happen if turn 0 is handled), 
        # all empty cells are valid.
        if not occupied:
            return [h for h, m in self.grid.cells.items() if m is None]
            
        # Collect all candidates within distance 2 of any occupied tile
        candidates = set()
        for cell in occupied:
            # Dist 1 (Neighbors)
            neighbors = cell.neighbors()
            candidates.update(neighbors)
            # Dist 2 (Neighbors of Neighbors)
            for n in neighbors:
                candidates.update(n.neighbors())
        
        # Filter for candidates that are actually on the board and empty
        valid = []
        for c in candidates:
            if c in self.grid.cells and self.grid.cells[c] is None:
                valid.append(c)
                
        return valid

    def get_agent_move(self):
        """
        Request a move from the current player's agent (if one exists).
        Returns (q, r) or None.
        """
        player = self.current_player()
        agent = self.agents.get(player)
        if agent:
            # Delegate decision making to the agent
            # We pass 'self' (the game instance) so the agent can inspect the board
            move_hex = agent.get_move(self)
            if move_hex:
                return move_hex.q, move_hex.r
        return None

    def play_move(self, q, r):
        """
        Attempts to play a move at coordinates (q, r).
        Returns: (Success (bool), Message (str))
        """
        if self.game_over:
            return False, "Game Over"
        
        cell = Hex(q, r)
        player = self.current_player()
        
        # 0. First Move Restriction
        if self.turn_index == 0 and cell != Hex(0, 0, 0):
             return False, "First move must be in the center"
        
        # 1. Place the marker on the grid
        # NEW RULE: Loose Adjacency w/ Distance 2
        # Unless the board is empty, you must place near (dist<=2) an existing marker.
        occupied = [h for h, m in self.grid.cells.items() if m is not None]
        if occupied:
            # Check if 'cell' is close enough to ANY occupied cell
            # Optimization: We just need ONE occupied cell within dist 2
            valid_adjacency = False
            for op in occupied:
                if cell.distance(op) <= 2:
                    valid_adjacency = True
                    break
            
            if not valid_adjacency:
                return False, "Must play within range of existing tiles"

        if not self.grid.place_marker(cell, player):
            return False, "Invalid Move"
        
        # 2. Calculate the new score for this player
        new_score, all_shapes = self.scorer.calculate_score(player)
        self.scores[player] = new_score
        
        # 3. Identify WHICH shapes are new this turn
        new_shapes_found = []
        current_shape_ids = set()
        
        for shape in all_shapes:
            # Create a unique ID for the shape: (type, set_of_cells)
            shape_id = (shape['type'], shape['cells'])
            current_shape_ids.add(shape_id)
            
            # If we haven't seen this shape ID before, it's new!
            if shape_id not in self.existing_shapes[player]:
                new_shapes_found.append(shape)
                
        # Update our memory of known shapes
        self.existing_shapes[player] = current_shape_ids
        
        # Update UI-facing state variables
        self.last_scoring_event = new_shapes_found
        self.last_turn_shapes[player] = new_shapes_found
        
        # Calculate how many points were gained just now
        score_diff = sum(s['points'] for s in new_shapes_found)
        self.last_turn_points[player] = score_diff 
        
        # Add to game log
        if score_diff > 0:
            self.log.append(f"{player} scored +{score_diff}!")
        
        # 4. Check if the game has ended
        self._check_end_condition()
        
        # 5. Advance turn (if game isn't over)
        if not self.game_over:
            self.turn_index += 1
            
        return True, "OK"

    def ai_move(self):
        """
        Trigger the current AI agent to move.
        This provides backward compatibility with the existing API.
        """
        move = self.get_agent_move()
        if move:
            self.play_move(move[0], move[1])

    def _check_end_condition(self):
        """
        Checks if the game should end based on score or board fullness.
        """
    def _check_end_condition(self):
        """
        Checks if the game should end based on turn limit or board fullness.
        """
        # Condition 1: Board Full
        if self.grid.is_full():
            self.game_over = True
            self._determine_winner()
            return
            
        # Condition 2: Max Rounds Reached OR Board Full (Equal Turns)
        # We want to ensure equal turns if possible.
        # If the board has an odd number of cells, we should stop 1 short of full
        # so the second player gets the last move.
        
        board_capacity = len(self.grid.cells)
        # If capacity is odd, max turns is capacity - 1
        effective_capacity = board_capacity if board_capacity % 2 == 0 else board_capacity - 1
        
        # Max turns based on rounds
        max_turns_rounds = self.max_rounds * 2
        
        # The game ends if we reach whichever limit is lower
        turn_limit = min(max_turns_rounds, effective_capacity)
        
        if self.turn_index >= turn_limit:
            self.game_over = True
            self._determine_winner()
            return

    def _determine_winner(self):
        # Simply compare scores
        s_red = self.scores['Red']
        s_blue = self.scores['Blue']
        if s_red > s_blue:
            self.winner = 'Red'
        elif s_blue > s_red:
            self.winner = 'Blue'
        else:
            self.winner = 'Draw'

    def get_state(self):
        """
        Returns the entire game state as a dictionary.
        This dictionary is converted to a JavaScript object for the frontend.
        """
        # Convert last scoring event shapes to a JSON-friendly format
        # (Sets cannot be serialized to JSON, so we convert them to lists of dicts)
        game_last_shapes = []
        for s in self.last_scoring_event:
            # s['cells'] is frozenset of Hex objects
            cells_json = [{'q': h.q, 'r': h.r, 's': h.s} for h in s['cells']]
            game_last_shapes.append({
                'type': s['type'],
                'points': s['points'],
                'cells': cells_json
            })

        # Serialize last_turn_shapes for both players
        last_turn_shapes_json = {'Red': [], 'Blue': []}
        for p in ['Red', 'Blue']:
            p_shapes = []
            for s in self.last_turn_shapes[p]:
                 cells_json = [{'q': h.q, 'r': h.r, 's': h.s} for h in s['cells']]
                 p_shapes.append({
                    'type': s['type'],
                    'points': s['points'],
                    'cells': cells_json
                 })
            last_turn_shapes_json[p] = p_shapes

        return {
            # Convert map keys "Hex(q,r,s)" to string "q,r,s" for JS
            'board': {
                f"{h.q},{h.r},{h.s}": m 
                for h, m in self.grid.cells.items()
            },
            'bonuses': {
                f"{h.q},{h.r},{h.s}": v 
                for h, v in self.grid.bonuses.items()
            },
            'scores': self.scores,
            'current_player': self.current_player(),
            'game_over': self.game_over,
            'winner': self.winner,
            'log': self.log[-5:], # send last 5 logs
            'last_scoring_event': game_last_shapes,
            'last_turn_shapes': last_turn_shapes_json,
            'max_rounds': self.max_rounds,
            'turn_index': self.turn_index,
            'total_turns': self.max_rounds * 2,
            'last_turn_points': self.last_turn_points
        }
