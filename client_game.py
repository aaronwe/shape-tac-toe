import js
from pyscript import when
from game import Game
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
    winning_score_val = js.document.getElementById('winning-score').value
    
    # Determine if AI is enabled (Mode '1' = 1 Player vs AI)
    ai_enabled = (player_mode == '1')
    
    # Parse winning score string to integer (or None for Unlimited)
    winning_score = None
    if winning_score_val and winning_score_val != "None":
        try:
            winning_score = int(winning_score_val)
        except:
            winning_score = 40
            
    # Initialize the Game Logic Class
    game_instance = Game(size=4, winning_score=winning_score)
    
    # Prepare the initial state to send to the UI
    # We use json.dumps to turn the Python Dict into a JSON String.
    # Then we parse it back in JS or let JS parse it.
    # Here, we parse it into a JS Object using js.JSON.parse so the JS function receives a real Object.
    state_json = json.dumps(get_state_dict())
    js.handleStateUpdate(js.JSON.parse(state_json))
    
    # Call a JS function to hide the setup modal
    js.hideModal()
    
    # Update the "Goal" text in the UI
    goal_text = "Unlimited" if winning_score is None else str(winning_score)
    js.document.getElementById('goal-display').innerText = goal_text
    
    # Tell the JS frontend if the AI is active (so it can block input during AI turns)
    js.setAiEnabled(ai_enabled)

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
        print(f"Move failed: {msg}")
        return
        
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
