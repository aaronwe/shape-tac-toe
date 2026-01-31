import js
from pyscript import when
from game import Game
from ai_player import EasyPlayer, GreedyPlayer, ThoughtfulPlayer, GeniusPlayer, MinimaxPlayer
import json

# Global game instance
# We need to store the game object in a global variable so it persists between function calls.
game_instance = None

def get_state_dict():
    """
    Helper to return the current game state as a Python dictionary.
    
    In PyScript, we often need to send data efficiently to JavaScript.
    Returning a pure Python dictionary is usually automatically converted to a JS Object by PyScript's proxy,
    but sometimes we use JSON strings to be absolutely safe and explicit.
    """
    if game_instance:
        return game_instance.get_state()
    return {"error": "Game not initialized"}

@when("click", "#start-game-btn")
def start_new_game(event=None):
    """
    Event Handler for the "Start New Game" button.
    The @when decorator connects this Python function to a DOM event.
    Target: The element with ID 'start-game-btn'.
    Event: 'click'.
    """
    global game_instance
    
    # Read configuration values directly from the HTML DOM using the 'js' module
    player_mode = js.document.getElementById('player-mode').value
    ai_difficulty_blue = js.document.getElementById('ai-difficulty-blue').value
    ai_difficulty_red = js.document.getElementById('ai-difficulty-red').value
    max_rounds_val = js.document.getElementById('game-length').value
    
    # Parse mode
    mode_str = str(player_mode).strip()
    
    player_agents = {}
    ai_players_list = []
    
    # Mode 0: AI vs AI (Both players are AI)
    if mode_str == '0':
        # Configure Red AI
        if ai_difficulty_red == 'easy':
            player_agents['Red'] = EasyPlayer('Red')
        elif ai_difficulty_red == 'greedy':
            player_agents['Red'] = GreedyPlayer('Red')
        elif ai_difficulty_red == 'thoughtful':
            player_agents['Red'] = ThoughtfulPlayer('Red')
        elif ai_difficulty_red == 'smart':
             player_agents['Red'] = MinimaxPlayer('Red', depth=2)
        elif ai_difficulty_red == 'genius':
             player_agents['Red'] = GeniusPlayer('Red')
        else:
             player_agents['Red'] = GreedyPlayer('Red')
             
        # Configure Blue AI
        if ai_difficulty_blue == 'easy':
            player_agents['Blue'] = EasyPlayer('Blue')
        elif ai_difficulty_blue == 'greedy':
            player_agents['Blue'] = GreedyPlayer('Blue')
        elif ai_difficulty_blue == 'thoughtful':
            player_agents['Blue'] = ThoughtfulPlayer('Blue')
        elif ai_difficulty_blue == 'smart':
             player_agents['Blue'] = MinimaxPlayer('Blue', depth=2)
        elif ai_difficulty_blue == 'genius':
             player_agents['Blue'] = GeniusPlayer('Blue')
        else:
             player_agents['Blue'] = GreedyPlayer('Blue')
             
        ai_players_list = ['Red', 'Blue']

    # Mode 1: 1 Player (Human vs AI)
    elif mode_str == '1':
        # Configure Blue AI only
        if ai_difficulty_blue == 'easy':
            player_agents['Blue'] = EasyPlayer('Blue')
        elif ai_difficulty_blue == 'greedy':
            player_agents['Blue'] = GreedyPlayer('Blue')
        elif ai_difficulty_blue == 'thoughtful':
            player_agents['Blue'] = ThoughtfulPlayer('Blue')
        elif ai_difficulty_blue == 'smart':
             player_agents['Blue'] = MinimaxPlayer('Blue', depth=2)
        elif ai_difficulty_blue == 'genius':
             player_agents['Blue'] = GeniusPlayer('Blue')
        else:
             player_agents['Blue'] = GreedyPlayer('Blue')
             
        ai_players_list = ['Blue']

    # Mode 2: 2 Players (Human vs Human)
    # No agents needed

    # Parse max rounds
    max_rounds = 25
    if max_rounds_val:
        try:
            max_rounds = int(max_rounds_val)
        except:
            max_rounds = 25
            
    # Tell the JS frontend which players are AI
    # We use json.dumps to ensure the list is passed as a valid JS array string, 
    # then parse it on the JS side or let JS receive it as a proxy. 
    # To be safest with PyScript/JS interop, sending a JSON string and parsing in JS is robust.
    # However, our script.js expects an array. Let's send a flexible JSON string.
    # Actually, let's just use the proxy but call it safely.
    # A safer bet: call a JS wrapper that takes a JSON string.
    # Or just rely on PyScript's conversion but move it up.
    
    # Let's use json.dumps and have a JS function parse it if needed.
    # But wait, setAiConfig expects 'players'. 
    # Let's modify setAiConfig in JS to handle either array or string? 
    # Or just pass a proxy.
    
    # Simplest fix: Move this to the TOP.
    # And convert to JSON string and parse in Python side? No.
    # js.setAiConfig(js.JSON.parse(json.dumps(ai_players_list))) works reliably.
    js.setAiConfig(js.JSON.parse(json.dumps(ai_players_list)))

    # Initialize the Game Logic Class
    game_instance = Game(size=6, max_rounds=max_rounds, player_agents=player_agents)
    
    # Hide the modal *before* starting the heavy lifting/animation
    js.hideModal()
    
    # Update the "Goal" text in the UI
    goal_display = js.document.getElementById('goal-display')
    if goal_display:
        goal_display.innerText = str(max_rounds)

    # Prepare the initial state to send to the UI
    state_json = json.dumps(get_state_dict())
    js.handleStateUpdate(js.JSON.parse(state_json))

def move(q, r):
    """
    Called by JavaScript when a user clicks a hex.
    Arguments: q, r (the axial coordinates of the clicked hex)
    """
    global game_instance
    if not game_instance:
        return
        
    # Attempt to play the move in the game logic
    success, msg = game_instance.play_move(q, r)
    if not success:
        return json.dumps({"error": msg})
        
    # If successful, return the new state as a JSON string to JS.
    # The JS side will parse this string.
    return json.dumps(get_state_dict())

def ai_move_py():
    """
    Called by JavaScript to trigger an AI move.
    """
    global game_instance
    if game_instance:
        game_instance.ai_move()
        return json.dumps(get_state_dict())
    return "{}"

def get_state_json():
    # Simple getter for the current state
    return json.dumps(get_state_dict())
    
# Expose functions to the global JavaScript namespace (window object).
# This allows 'window.py_move(q, r)' to work in index.html/script.js.
js.window.py_move = move
js.window.py_ai_move = ai_move_py
js.window.py_get_state = get_state_json
js.window.py_start_game = start_new_game 
# Note: start_new_game is already bound via @when, but exposing it explicitly doesn't hurt.
