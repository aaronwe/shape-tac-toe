# Shape Tac Toe

A hexagonal strategy board game where players compete to form geometric shapes. Run entirely in the browser using **PyScript**.

## 🎮 Game Rules

Two players (Red and Blue) take turns placing markers on a hexagonal grid. The goal is to reach the winning score (default: 40 points) by forming specific patterns.

### Scoring
*   **Line (3+)**: 3 or more markers in a straight line.
    *   *Points*: 1 pt for 3, +1 for each additional marker.
*   **Loop (Ring)**: 6 markers surrounding a single center hex.
    *   *Points*: 6 pts.
*   **Triangle**: A filled triangle of markers.
    *   *Points*: Side length 2 = 1 pt. Larger sizes = Side length pts (e.g., Size 3 = 3 pts).
*   **Hollow Shape**: An outline of markers with an empty interior.
    *   *Points*: 3x3 outline = 4 pts, 4x4 outline = 8 pts.

### Winning
The first player to reach the target score triggers the end game.
*   **Fairness Rule**: If Red reaches the target first, Blue gets one final turn to try and beat Red's score.
*   The game can also end if the board is completely full.

---

## 🏗️ Technical Architecture

This project demonstrates a **Serverless Web App** architecture using **PyScript**. The complex game logic remains in Python, while the UI is handled by standard HTML/CSS/JS.

### Tech Stack
*   **Core Logic**: Python 3 (running in-browser via PyScript/WASM).
*   **Frontend**: HTML5, CSS3, Vanilla JavaScript.
*   **Runtime**: PyScript (2024.1.1).

### Key Components

#### 1. Python Game Engine
*   **`hex_grid.py`**: Implements a Cube Coordinate System (`q, r, s`) for the hexagonal grid. Handles neighbor calculations and board storage.
*   **`scorer.py`**: The "brain" of the operation. Contains algorithms to detect geometric shapes (Lines, Loops, Triangles, Rhombuses) on the grid and calculate scores.
*   **`game.py`**: Manages the state machine (turns, scores, win conditions) and AI decision-making.

#### 2. The PyScript Bridge
*   **`client_game.py`**: Acts as the interface between the Python backend and the JavaScript frontend.
    *   Exposes Python functions `py_move`, `py_ai_move`, and `py_start_game` to the browser's `window` object.
    *   Uses `js` module to read values from the DOM.
*   **`pyscript.toml`**: Configuration file that maps the local Python files to the virtual file system in the browser.

#### 3. Frontend
*   **`index.html`**: Loads the PyScript runtime and defines the UI structure.
*   **`script.js`**: Handles user interactions (clicks), manages the SVG rendering of the hex grid, and updates the DOM based on the game state returned by Python.

---

## 🚀 How to Run
Since this uses PyScript, it runs entirely in your web browser. However, due to browser security policies (CORS) regarding loading local files, you cannot just double-click `index.html`.

1.  **Start a local server**:
    ```bash
    python3 -m http.server
    ```
2.  **Open in Browser**:
    Visit `http://localhost:8000`

## 🧠 AI Implementation
The game includes a basic AI opponent:
*   **Simulation**: The AI copies the current board state.
*   **Evaluation**: It simulates placing a marker in every available spot.
*   **Scoring**: It runs the full `Scorer` logic on the simulated move.
*   **Selection**: It chooses the move that yields the highest immediate score.
