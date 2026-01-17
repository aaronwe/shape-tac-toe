import js
from pyscript import when
from game import Game
import json

# Global game instance
game_instance = None

def get_state_dict():
    """Helper to return state as a Python dict (PyScript converts to JS object automatically proxy-ish, 
    but explicit json serialization or dict conversion is safer for complex objects if we want strict JS interop compatibility).
    Actually, PyScript now handles dicts -> JS Objects quite well.
    """
    if game_instance:
        return game_instance.get_state()
    return {"error": "Game not initialized"}

@when("click", "#start-game-btn")
def start_new_game(event=None):
    global game_instance
    
    # Read from DOM
    player_mode = js.document.getElementById('player-mode').value
    winning_score_val = js.document.getElementById('winning-score').value
    
    # Logic from app.py
    ai_enabled = (player_mode == '1')
    # pass ai_enabled to JS? app.py didn't store it in Game, script.js held it
    # We'll just init the game logic here
    
    winning_score = None
    if winning_score_val and winning_score_val != "None":
        try:
            winning_score = int(winning_score_val)
        except:
            winning_score = 40
            
    game_instance = Game(size=4, winning_score=winning_score)
    
    # Signal JS to update UI
    # We can call a JS function exposed on window
    js.handleStateUpdate(js.JSON.parse(json.dumps(get_state_dict())))
    
    # Hide modal
    js.hideModal()
    
    # Update Goal text in UI
    goal_text = "Unlimited" if winning_score is None else str(winning_score)
    js.document.getElementById('goal-display').innerText = goal_text
    
    # Set AI flag in JS
    js.setAiEnabled(ai_enabled)

def move(q, r):
    global game_instance
    if not game_instance:
        return
        
    success, msg = game_instance.play_move(q, r)
    if not success:
        print(f"Move failed: {msg}")
        return
        
    # Return state to JS
    return json.dumps(get_state_dict())

def ai_move_py():
    global game_instance
    if game_instance:
        game_instance.ai_move()
        return json.dumps(get_state_dict())
    return "{}"

def get_state_json():
    return json.dumps(get_state_dict())
    
# Expose functions to global window for JS to call
js.window.py_move = move
js.window.py_ai_move = ai_move_py
js.window.py_get_state = get_state_json
js.window.py_start_game = start_new_game 
# Note: start_new_game is already bound via @when, but exposing it explicitly doesn't hurt if we need manual call
