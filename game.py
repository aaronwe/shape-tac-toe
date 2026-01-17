from hex_grid import HexGrid, Hex
from scorer import Scorer
import random

class Game:
    def __init__(self, size=4, winning_score=40):
        self.grid = HexGrid(radius=size)
        self.scorer = Scorer(self.grid)
        self.players = ['Red', 'Blue']
        self.turn_index = 0
        self.scores = {'Red': 0, 'Blue': 0}
        self.winner = None
        self.game_over = False
        self.log = []
        self.winning_score = winning_score
        
        # Track known shapes to identify NEW ones
        self.existing_shapes = {'Red': set(), 'Blue': set()}
        self.last_scoring_event = [] # List of new shapes from the last move
        self.last_turn_points = {'Red': 0, 'Blue': 0} # Points scored in the most recent turn for each player
        self.last_turn_shapes = {'Red': [], 'Blue': []} # Shapes scored in the most recent turn for each player
        
        self.final_turn = False 

    def current_player(self):
        return self.players[self.turn_index % 2]

    def play_move(self, q, r):
        if self.game_over:
            return False, "Game Over"
        
        cell = Hex(q, r)
        player = self.current_player()
        
        if not self.grid.place_marker(cell, player):
            return False, "Invalid Move"
        
        # Calculate score and identify NEW shapes
        new_score, all_shapes = self.scorer.calculate_score(player)
        self.scores[player] = new_score
        
        # Find new shapes
        new_shapes_found = []
        current_shape_ids = set()
        
        for shape in all_shapes:
            shape_id = (shape['type'], shape['cells'])
            current_shape_ids.add(shape_id)
            
            if shape_id not in self.existing_shapes[player]:
                new_shapes_found.append(shape)
                
        self.existing_shapes[player] = current_shape_ids
        self.existing_shapes[player] = current_shape_ids
        self.last_scoring_event = new_shapes_found
        self.last_turn_shapes[player] = new_shapes_found
        
        score_diff = sum(s['points'] for s in new_shapes_found)
        self.last_turn_points[player] = score_diff # Update last turn points
        
        if score_diff > 0:
            self.log.append(f"{player} scored +{score_diff}!")
        
        self._check_end_condition()
        
        if not self.game_over:
            self.turn_index += 1
            
        return True, "OK"

    def ai_move(self):
        if self.game_over:
            return
            
        player = self.current_player()
        valid_moves = [h for h, m in self.grid.cells.items() if m is None]
        if not valid_moves:
            return 
            
        best_move = None
        best_score = -1
        
        current_score = self.scores[player]
        random.shuffle(valid_moves)
        
        for move in valid_moves:
             # Simulate
            self.grid.cells[move] = player
            score, _ = self.scorer.calculate_score(player)
            # Revert
            self.grid.cells[move] = None
            
            if score > best_score:
                best_score = score
                best_move = move
                
        if best_move:
            self.play_move(best_move.q, best_move.r)

    def _check_end_condition(self):
        # FAIRNESS LOGIC:
        # If it's the "Final Turn" (initiated by Red reaching winning score), then the game is over after this turn (Blue's turn).
        if self.final_turn:
            self.game_over = True
            self._determine_winner()
            return

        if self.grid.is_full():
            self.game_over = True
            self._determine_winner()
            return
            
        if self.winning_score is None:
            return 
            
        current = self.current_player()
        red_score = self.scores['Red']
        blue_score = self.scores['Blue']

        if red_score >= self.winning_score or blue_score >= self.winning_score:
            if current == 'Blue': 
                self.game_over = True
                self._determine_winner()
            else:
                self.final_turn = True
                self.log.append("Last Turn for Blue!")

    def _determine_winner(self):
        s_red = self.scores['Red']
        s_blue = self.scores['Blue']
        if s_red > s_blue:
            self.winner = 'Red'
        elif s_blue > s_red:
            self.winner = 'Blue'
        else:
            self.winner = 'Draw'

    def get_state(self):
        # Convert last scoring event to JSON friendly
        game_last_shapes = []
        for s in self.last_scoring_event:
            # s['cells'] is frozenset of Hex
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
            'board': {
                f"{h.q},{h.r},{h.s}": m 
                for h, m in self.grid.cells.items()
            },
            'scores': self.scores,
            'current_player': self.current_player(),
            'game_over': self.game_over,
            'winner': self.winner,
            'log': self.log[-5:],
            'last_scoring_event': game_last_shapes,
            'last_turn_shapes': last_turn_shapes_json,
            'final_turn': self.final_turn,
            'winning_score': self.winning_score,
            'last_turn_points': self.last_turn_points
        }
