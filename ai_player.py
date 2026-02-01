import random
import copy

class AIPlayer:
    """
    Base class for AI Players.
    """
    def __init__(self, color):
        self.color = color

    def get_move(self, game):
        """
        Returns a tuple (q, r) for the selected move.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("AIPlayer subclasses must implement get_move")

class RandomPlayer(AIPlayer):
    """
    Selects a random valid move from the board.
    """
    def get_move(self, game):
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
        return random.choice(valid_moves)

class GreedyPlayer(AIPlayer):
    """
    Simulates one move ahead and selects the one with the highest immediate score.
    """
    def get_move(self, game):
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
        
        best_move = None
        best_score = -1
        
        # Shuffle to break ties randomly
        random.shuffle(valid_moves)
        
        for move in valid_moves:
            # 1. Simulate
            game.grid.cells[move] = self.color
            
            # 2. Score
            # Use fast scoring calculation
            score, _ = game.scorer.calculate_score(self.color, just_points=True)
            
            # 3. Undo
            game.grid.cells[move] = None
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move

class MinimaxPlayer(AIPlayer):
    """
    Uses Minimax algorithm with Alpha-Beta pruning AND Beam Search to look ahead.
    """
    def __init__(self, color, depth=2, beam_width=6):
        super().__init__(color)
        self.depth = depth
        self.beam_width = beam_width
        self.transposition_table = {}

    def get_move(self, game):
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None

        # Pre-sort moves at root for better efficiency (Best-First)
        # Even if we don't prune at root (to avoid missing a win), sorting helps Alpha-Beta.
        sorted_moves = self._sort_moves_by_heuristic(game, valid_moves, self.color)
        
        # Apply pruning at root if needed? 
        # Usually checking top 20 at root is fine.
        moves_to_search = sorted_moves[:max(self.beam_width * 2, 20)]

        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        
        best_val = float('-inf')
        
        for move in moves_to_search:
            # Apply Move
            game.grid.cells[move] = self.color
            
            # Recurse
            val = self._minimax(game, self.depth - 1, False, alpha, beta)
            
            # Undo Move
            game.grid.cells[move] = None
            
            if val > best_val:
                best_val = val
                best_move = move
                
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
                
        return best_move

    def _minimax(self, game, depth, is_maximizing, alpha, beta):
        # 1. Transposition Table Lookup
        # Create a simple hash/key of the board state.
        # Ideally, we'd use Zobrist hashing, but for now, stringifying the cells is "okay" given the grid size.
        # Actually, let's just use the set of (cell, marker) tuples which is hashable.
        # Optimization: We only need to key off the OCCUPIED cells.
        board_key = (frozenset(game.grid.cells.items()), depth, is_maximizing)
        if board_key in self.transposition_table:
            return self.transposition_table[board_key]

        if depth == 0 or game.grid.is_full():
            val = self._evaluate(game)
            self.transposition_table[board_key] = val
            return val
            
        valid_moves = game.get_valid_moves()
        
        # ---------------------------------------------------------
        # BEAM SEARCH / FORWARD PRUNING
        # ---------------------------------------------------------
        # Instead of checking ALL moves, score them cheaply and check only Top K.
        # Heuristic: Immediate score (Greedy).
        current_turn_color = self.color if is_maximizing else ('Blue' if self.color == 'Red' else 'Red')
        
        sorted_moves = self._sort_moves_by_heuristic(game, valid_moves, current_turn_color)
        
        # Beam Width: Restrict branching factor
        moves_to_search = sorted_moves[:self.beam_width]
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in moves_to_search:
                game.grid.cells[move] = self.color
                eval_score = self._minimax(game, depth - 1, False, alpha, beta)
                game.grid.cells[move] = None
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            self.transposition_table[board_key] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            opponent = 'Blue' if self.color == 'Red' else 'Red'
            for move in moves_to_search:
                game.grid.cells[move] = opponent
                eval_score = self._minimax(game, depth - 1, True, alpha, beta)
                game.grid.cells[move] = None
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            self.transposition_table[board_key] = min_eval
            return min_eval

    def _sort_moves_by_heuristic(self, game, moves, player_color):
        """
        Sorts moves by their immediate score impact (Greedy Heuristic).
        Returns list of moves, sorted descending by score.
        """
        scored = []
        for move in moves:
            game.grid.cells[move] = player_color
            # OPTIMIZATION: Use just_points=True to skip shape generation
            s, _ = game.scorer.calculate_score(player_color, just_points=True)
            game.grid.cells[move] = None
            scored.append((s, move))
            
        # Sort descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in scored]

    def _evaluate(self, game):
        """
        Simple heuristic: (My Score - Opponent Score)
        """
        # OPTIMIZATION: Use just_points=True
        my_score, _ = game.scorer.calculate_score(self.color, just_points=True)
        opponent = 'Blue' if self.color == 'Red' else 'Red'
        op_score, _ = game.scorer.calculate_score(opponent, just_points=True)
        return my_score - op_score

class EasyPlayer(AIPlayer):
    """
    "Easy": Like Greedy, but randomly picks between the best or second-best move.
    """
    def get_move(self, game):
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
        
        # Calculate score for every move
        scored_moves = []
        random.shuffle(valid_moves) # Shuffle first for tie-breaking
        
        for move in valid_moves:
            game.grid.cells[move] = self.color
            # Optimization: Use fast scoring here too
            score, _ = game.scorer.calculate_score(self.color, just_points=True)
            game.grid.cells[move] = None
            scored_moves.append((score, move))
            
        # Sort by score descending
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        
        # Pick top 2
        top_candidates = scored_moves[:2]
        
        if not top_candidates:
            return None
            
        # Pick randomly between them
        chosen = random.choice(top_candidates)
        return chosen[1]

class ThoughtfulPlayer(AIPlayer):
    """
    "Thoughtful": 50% chance of Depth 1 (Greedy), 50% chance of Depth 2 (Minimax).
    """
    def __init__(self, color):
        super().__init__(color)
        self.greedy = GreedyPlayer(color)
        self.minimax = MinimaxPlayer(color, depth=2)
        
    def get_move(self, game):
        # 50% chance check
        if random.random() < 0.5:
            return self.greedy.get_move(game)
        else:
            return self.minimax.get_move(game)

class GeniusPlayer(MinimaxPlayer):
    """
    "Genius": Minimax with Depth 3 and Beam Width 5.
    """
    def __init__(self, color):
        super().__init__(color, depth=3, beam_width=5)

class SmartPlayer(MinimaxPlayer):
    """
    "Smart": Minimax with standard constraints (Depth 2).
    """
    def __init__(self, color):
        super().__init__(color, depth=2)
