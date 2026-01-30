import argparse
import time
from game import Game
from ai_player import RandomPlayer, GreedyPlayer, MinimaxPlayer, EasyPlayer, ThoughtfulPlayer, GeniusPlayer

def get_agent(name, color):
    name = name.lower()
    if name == 'random':
        return RandomPlayer(color)
    elif name == 'greedy':
        return GreedyPlayer(color)
    elif name == 'minimax':
        return MinimaxPlayer(color, depth=2)
    elif name == 'easy':
        return EasyPlayer(color)
    elif name == 'thoughtful':
        return ThoughtfulPlayer(color)
    elif name == 'genius':
        return GeniusPlayer(color)
    else:
        raise ValueError(f"Unknown agent type: {name}")

def run_simulation(num_games, p1_type, p2_type, size=6, verbose=False):
    results = {'Red': 0, 'Blue': 0, 'Draw': 0}
    total_turns = 0
    total_score_red = 0
    total_score_blue = 0
    shape_counts = {}
    
    start_time = time.time()
    
    for i in range(num_games):
        # Setup Agents
        agents = {
            'Red': get_agent(p1_type, 'Red'),
            'Blue': get_agent(p2_type, 'Blue')
        }
        
        game = Game(size=size, max_rounds=25, player_agents=agents)
        
        # Game Loop
        while not game.game_over:
            # Current player's agent decides move
            q, r = game.get_agent_move()
            
            # Execute move
            success, msg = game.play_move(q, r)
            if not success:
                print(f"Game {i}: Agent {game.current_player()} tried invalid move ({q},{r}): {msg}")
                break
                
            # Track shapes
            for s in game.last_scoring_event:
                stype = s['type']
                shape_counts[stype] = shape_counts.get(stype, 0) + 1
        
        # Collect Stats
        results[game.winner] += 1
        total_turns += game.turn_index
        total_score_red += game.scores['Red']
        total_score_blue += game.scores['Blue']
        
        print(f"Game {i+1}/{num_games}: Winner={game.winner}, Score={game.scores['Red']}-{game.scores['Blue']}, Turns={game.turn_index}")        
            
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*40)
    print(f"SIMULATION REPORT: {p1_type} (Red) vs {p2_type} (Blue)")
    print(f"Games: {num_games}")
    print(f"Time Taken: {duration:.2f}s ({duration/num_games:.3f}s/game)")
    print("="*40)
    print(f"Red Wins:  {results['Red']} ({results['Red']/num_games*100:.1f}%)")
    print(f"Blue Wins: {results['Blue']} ({results['Blue']/num_games*100:.1f}%)")
    print(f"Draws:     {results['Draw']} ({results['Draw']/num_games*100:.1f}%)")
    print("-" * 40)
    print(f"Avg Turns: {total_turns/num_games:.1f}")
    print(f"Avg Score Red:  {total_score_red/num_games:.1f}")
    print(f"Avg Score Blue: {total_score_blue/num_games:.1f}")
    
    # Calculate Board Usage Stats
    # Radius 4 = 61 hexes? No, Radius 4 = 1 + 6*sum(1..4) = 1 + 60 = 61.
    # Radius 6 = 1 + 6*sum(1..6) = 1 + 6*21 = 127 hexes.
    # We should dynamically get the board size from the game instance if possible, or just trust the cells dict length.
    total_cells = len(game.grid.cells)
    total_filled = total_turns # Since each turn places 1 marker (usually)
    # Wait, total_turns across ALL games. 
    # Average turns per game = Average filled cells per game (assuming no passes/removals)
    # So Avg Usage % = (Avg Turns / Total Cells) * 100
    
    avg_filled = total_turns / num_games
    usage_pct = (avg_filled / total_cells) * 100
    print(f"Avg Board Usage: {avg_filled:.1f}/{total_cells} ({usage_pct:.1f}%)")
    
    print("-" * 40)
    print("Shape Frequencies (Total across all games):")
    # Sort by frequency
    sorted_shapes = sorted(shape_counts.items(), key=lambda x: x[1], reverse=True)
    for s, c in sorted_shapes:
        print(f"  {s}: {c} ({c/num_games:.1f} per game)")
    print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Shape Tac Toe Simulations")
    parser.add_argument("--games", type=int, default=10, help="Number of games to simulate")
    parser.add_argument("--size", type=int, default=6, help="Board Radius")
    parser.add_argument("--p1", type=str, default="random", help="Player 1 Strategy")
    parser.add_argument("--p2", type=str, default="greedy", help="Player 2 Strategy")
    parser.add_argument("--verbose", action="store_true", help="Print details for each game")
    
    args = parser.parse_args()
    
    run_simulation(args.games, args.p1, args.p2, args.size, args.verbose)
