from flask import Flask, render_template, jsonify, request
from game import Game

app = Flask(__name__)

# Global game instance
game_instance = Game(size=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new_game', methods=['POST'])
def new_game():
    global game_instance
    data = request.json or {}
    size = data.get('size', 4)
    winning_score = data.get('winning_score')
    
    # Handle winning_score: frontend might send "None" string or null or 40.
    if winning_score == "None" or winning_score is None:
         winning_score = None
    else:
         try:
             winning_score = int(winning_score)
         except:
             winning_score = 40 # Default fallback
             
    game_instance = Game(size=size, winning_score=winning_score)
    return jsonify(game_instance.get_state())

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(game_instance.get_state())

@app.route('/api/move', methods=['POST'])
def move():
    data = request.json
    q = data.get('q')
    r = data.get('r')
    
    if q is None or r is None:
        return jsonify({'error': 'Missing coordinates'}), 400
        
    success, msg = game_instance.play_move(q, r)
    if not success:
        return jsonify({'error': msg}), 400
        
    return jsonify(game_instance.get_state())

@app.route('/api/ai_move', methods=['POST'])
def ai_move():
    game_instance.ai_move()
    return jsonify(game_instance.get_state())

if __name__ == '__main__':
    # Port 5000 is often taken by AirPlay on macOS, using 5001
    app.run(debug=True, port=5001)
