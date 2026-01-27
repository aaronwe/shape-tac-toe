from hex_grid import HexGrid, Hex
from scorer import Scorer
import random

class Game:
    """
    The main Controller for the Shape Tac Toe game.
    
    This class manages:
    1. The Game Loop (whose turn is it?)
    2. The Board State (placed markers)
    3. The Scores (calculating and updating)
    4. The Win Conditions
    """
    def __init__(self, size=4, winning_score=40):
        # Initialize the hexagonal grid
        self.grid = HexGrid(radius=size)
        # Initialize the scorer with our grid
        self.scorer = Scorer(self.grid)
        
        # Player configuration
        self.players = ['Red', 'Blue']
        self.turn_index = 0
        self.scores = {'Red': 0, 'Blue': 0}
        
        # Game status flags
        self.winner = None
        self.game_over = False
        self.log = [] # A list of string messages for the UI
        self.winning_score = winning_score
        
        # Tracking "New" Shapes:
        # We need to remember which shapes we've already scored so we don't
        # score the same Triangle twice every turn.
        self.existing_shapes = {'Red': set(), 'Blue': set()}
        
        # Temporary state for the UI (to show animations)
        self.last_scoring_event = [] # List of new shapes from the last move
        self.last_turn_points = {'Red': 0, 'Blue': 0} # Points scored in the most recent turn for each player
        self.last_turn_shapes = {'Red': [], 'Blue': []} # Shapes scored in the most recent turn for each player
        
        # Fairness flag: If Red wins, Blue gets one last turn.
        self.final_turn = False 

    def current_player(self):
        # Returns 'Red' or 'Blue' based on the turn index.
        # Even numbers = Red, Odd numbers = Blue.
        return self.players[self.turn_index % 2]

    def play_move(self, q, r):
        """
        Attempts to play a move at coordinates (q, r).
        Returns: (Success (bool), Message (str))
        """
        if self.game_over:
            return False, "Game Over"
        
        cell = Hex(q, r)
        player = self.current_player()
        
        # 1. Place the marker on the grid
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
        A simple Greedy AI.
        It simulates every possible valid move and chooses the one that gives the most immediate points.
        """
        if self.game_over:
            return
            
        player = self.current_player()
        
        # Find all empty spots
        valid_moves = [h for h, m in self.grid.cells.items() if m is None]
        if not valid_moves:
            return 
            
        best_move = None
        best_score = -1
        
        current_score = self.scores[player]
        
        # Shuffle moves so the AI doesn't always pick the top-left one in case of ties
        random.shuffle(valid_moves)
        
        for move in valid_moves:
             # Simulation Step:
             # 1. Pretend to place the marker
            self.grid.cells[move] = player
            
            # 2. Check the score
            score, _ = self.scorer.calculate_score(player)
            
            # 3. Revert the change (Clean up!)
            self.grid.cells[move] = None
            
            # 4. Compare
            if score > best_score:
                best_score = score
                best_move = move
        
        # Execute the best move found
        if best_move:
            self.play_move(best_move.q, best_move.r)

    def _check_end_condition(self):
        """
        Checks if the game should end based on score or board fullness.
        """
        # FAIRNESS LOGIC:
        # If it's the "Final Turn" (initiated by Red reaching winning score), then the game is over after this turn (Blue's turn).
        if self.final_turn:
            self.game_over = True
            self._determine_winner()
            return

        # Condition 1: Board Full
        if self.grid.is_full():
            self.game_over = True
            self._determine_winner()
            return
            
        if self.winning_score is None:
            return 
            
        current = self.current_player()
        red_score = self.scores['Red']
        blue_score = self.scores['Blue']

        # Condition 2: Score Limit Reached
        if red_score >= self.winning_score or blue_score >= self.winning_score:
            if current == 'Blue': 
                # If Blue triggered the win (or matched Red), game ends immediately
                self.game_over = True
                self._determine_winner()
            else:
                # If Red triggered the win, Blue gets one chance to catch up
                self.final_turn = True
                self.log.append("Last Turn for Blue!")

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
            'scores': self.scores,
            'current_player': self.current_player(),
            'game_over': self.game_over,
            'winner': self.winner,
            'log': self.log[-5:], # send last 5 logs
            'last_scoring_event': game_last_shapes,
            'last_turn_shapes': last_turn_shapes_json,
            'final_turn': self.final_turn,
            'winning_score': self.winning_score,
            'last_turn_points': self.last_turn_points
        }
