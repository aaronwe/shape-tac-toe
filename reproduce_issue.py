from game import Game

def test_game_length():
    print("Testing Game Length Logic...")
    
    # 1 Round = 2 Turns.
    # Expectation: Game ends after 2 moves.
    g = Game(size=4, max_rounds=1) 
    
    print(f"Max Rounds: {g.max_rounds}")
    
    # Move 0 (Red)
    print(f"Turn {g.turn_index}: Playing Move...")
    g.play_move(0, 0)
    print(f"  -> Game Over? {g.game_over}")
    
    if g.game_over:
        print("FAIL: Game ended too early.")
        return

    # Move 1 (Blue)
    print(f"Turn {g.turn_index}: Playing Move...")
    g.play_move(0, 1) # Just play somewhere valid
    print(f"  -> Game Over? {g.game_over}")
    
    if g.game_over:
        print("SUCCESS: Game ended exactly after 2 moves.")
    else:
        print("FAIL: Game did NOT end after 2 moves.")
        
        # Move 2 (Red - Extra Turn)
        print(f"Turn {g.turn_index}: Playing Move (Extra)...")
        g.play_move(1, 0)
        print(f"  -> Game Over? {g.game_over}")
        
        if g.game_over:
            print("CONFIRMED BUG: Game ended 1 turn late.")
        else:
             print("FAIL: Game still going???")

if __name__ == "__main__":
    test_game_length()
