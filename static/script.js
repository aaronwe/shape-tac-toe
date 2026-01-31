// --------------------------------------------------------------------------
// Configuration Constants
// --------------------------------------------------------------------------
const HEX_SIZE = 25; // Size of each hexagon in pixels
const BOARD_RADIUS = 4; // Not strictly used for rendering, but matches Python logic
const VIEW_WIDTH = 600;
const VIEW_HEIGHT = 600;
// Center coordinates to offset drawing (0,0 in math -> center of SVG)
const CENTER_X = VIEW_WIDTH / 2;
const CENTER_Y = VIEW_HEIGHT / 2;

// --------------------------------------------------------------------------
// Global State Storage
// --------------------------------------------------------------------------
let currentState = null; // Stores the latest game state object from Python
let aiEnabled = false;   // Flag to prevent clicking while AI thinks
let previousScores = { 'Red': 0, 'Blue': 0 }; // Track score changes for animation
let isAnimating = false; // Flag to block interaction during score animations

/**
 * Called by Python to enabling/disabling AI mode.
 */
window.setAiEnabled = function (val) {
    aiEnabled = val;
}

// --------------------------------------------------------------------------
// Initialization
// --------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // 1. Show the "New Game" modal immediately when page loads
    showModal();

    // 2. Attach click listener to "Game Options" button
    document.getElementById('open-new-game-btn').addEventListener('click', () => {
        showModal();
    });

    // Note: The "Start Game" button in the modal is handled by Python's @when decorator!

    // 3. Attach listeners for the collapsible Score Logs
    const logToggleRed = document.getElementById('toggle-red');
    if (logToggleRed) {
        logToggleRed.addEventListener('click', () => toggleLog('red'));
    }

    const logToggleBlue = document.getElementById('toggle-blue');
    if (logToggleBlue) {
        logToggleBlue.addEventListener('click', () => toggleLog('blue'));
    }
});

function showModal() {
    document.getElementById('new-game-modal').classList.add('active');
}

function hideModal() {
    document.getElementById('new-game-modal').classList.remove('active');
}

// --------------------------------------------------------------------------
// State Management (The Bridge between Python and JS)
// --------------------------------------------------------------------------

/**
 * This is the main function called by Python to update the UI.
 * @param {Object} state - The game state object sent from Python.
 */
function handleStateUpdate(state) {
    if (state.error) {
        console.error(state.error);
        showErrorPopup(state.error);
        return;
    }

    const oldState = currentState;
    currentState = state;

    // 1. Render the board (markers)
    // We render markers immediately so the user sees their move.
    renderBoard(state);

    // 2. Update logs if there are new shapes
    if (state.last_turn_shapes) {
        updateScoreLog('red', state.last_turn_shapes.Red);
        updateScoreLog('blue', state.last_turn_shapes.Blue);
    }

    // 3. Handle Animations
    // If scoring happened (last_scoring_event has items), we play a sequence.
    if (state.last_scoring_event && state.last_scoring_event.length > 0) {
        animateScoringSequence(state.last_scoring_event, state);
    } else {
        // No scoring? Just update score numbers immediately.
        updateUI(state);

        // If it's the AI's turn, trigger it (after a short delay for realism)
        checkAiTurn();

        // Cleanup if game over
        if (state.game_over) {
            document.querySelectorAll('.hex-scoring').forEach(el => el.classList.remove('hex-scoring'));
        }
    }
}

/**
 * Async function to play animations one by one.
 * We use 'await' to pause execution so the user can see each shape light up.
 */
async function animateScoringSequence(shapes, state) {
    isAnimating = true;

    // Iterate through every shape scored in this move
    for (const shape of shapes) {
        // 1. Highlight the specific hexagons for this shape
        const shapeCells = shape.cells.map(c => `${c.q},${c.r}`);
        highlightHexes(shapeCells, true);

        // 2. Show a floating label (+4, +6, etc.) at the center of the shape
        const center = calculateShapeCenter(shape.cells);
        showShapeLabel(center, `+${shape.points}`);

        // 3. Pause for 800ms
        await wait(800);

        // 4. Cleanup: Remove highlight and label
        highlightHexes(shapeCells, false);
        removeShapeLabels();

        // Short pause between shapes
        await wait(200);
    }

    isAnimating = false;
    updateUI(state); // Finally update the score counters to the final value
    checkAiTurn();
}

/**
 * Adds the 'hex-scoring' CSS class to a list of hex coordinates.
 */
function highlightHexes(cellKeys, active) {
    const svg = document.getElementById('hex-grid');

    cellKeys.forEach(k => {
        // Find the polygon with the matching data-key
        const poly = svg.querySelector(`polygon[data-key="${k}"]`);
        if (poly) {
            if (active) poly.classList.add('hex-scoring');
            else poly.classList.remove('hex-scoring');
        }
    });
}

/**
 * Creates a floating text label on the board.
 */
function showShapeLabel(pos, text) {
    const container = document.getElementById('game-board');
    const label = document.createElement('div');
    label.className = 'shape-score-label';
    label.innerText = text;
    // Set absolute position based on calculated pixel coordinates
    label.style.left = `${pos.x}px`;
    label.style.top = `${pos.y}px`;

    container.appendChild(label);
}

function removeShapeLabels() {
    const container = document.getElementById('game-board');
    const labels = container.querySelectorAll('.shape-score-label');
    labels.forEach(l => l.remove());
}

/**
 * Averages the x and y coordinates of a list of hexes to find the visual center.
 */
function calculateShapeCenter(cells) {
    let sumX = 0, sumY = 0;
    cells.forEach(c => {
        const p = hexToPixel(c.q, c.r);
        sumX += p.x;
        sumY += p.y;
    });
    return { x: sumX / cells.length, y: sumY / cells.length };
}

// Simple Promise wrapper for setTimeout to make async/await work
function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// --------------------------------------------------------------------------
// AI Handling
// --------------------------------------------------------------------------
function checkAiTurn() {
    // If it's Blue's turn AND AI is enabled AND game isn't over...
    if (aiEnabled && currentState && currentState.current_player === 'Blue' && !currentState.game_over && !isAnimating) {
        setTimeout(() => {
            // Call the Python function 'py_ai_move'
            if (window.py_ai_move) {
                const stateRaw = window.py_ai_move();
                if (stateRaw) {
                    // Update JS with the result from Python
                    handleStateUpdate(JSON.parse(stateRaw));
                }
            }
        }, 500); // 500ms delay for "thinking" time
    }
}

// --------------------------------------------------------------------------
// UI Rendering
// --------------------------------------------------------------------------
function updateUI(state) {
    // Animate the score numbers counting up
    animateScore('score-red', previousScores['Red'], state.scores['Red'], 'card-red');
    animateScore('score-blue', previousScores['Blue'], state.scores['Blue'], 'card-blue');

    previousScores = { ...state.scores };

    // Update Last Turn text
    if (state.last_turn_points) {
        document.getElementById('last-turn-red').innerText = `Last Turn: ${state.last_turn_points['Red']}`;
        document.getElementById('last-turn-blue').innerText = `Last Turn: ${state.last_turn_points['Blue']}`;
    }

    const turnDiv = document.getElementById('turn-indicator');
    const msgDiv = document.getElementById('message-area');

    // Visual active state for player cards
    document.getElementById('card-red').classList.toggle('active-turn', state.current_player === 'Red' && !state.game_over);
    document.getElementById('card-blue').classList.toggle('active-turn', state.current_player === 'Blue' && !state.game_over);

    // Update body class for global hover colors (controls which color hexes turn on hover)
    document.body.className = '';
    if (!state.game_over && !isAnimating) {
        document.body.classList.add(state.current_player === 'Red' ? 'turn-red' : 'turn-blue');
    }

    // Handle Game Over or Next Turn messages
    if (state.game_over) {
        turnDiv.innerText = "Game Over!";
        msgDiv.innerText = `Winner: ${state.winner}`;
        // Clear any stuck highlights
        document.querySelectorAll('.hex-scoring').forEach(el => el.classList.remove('hex-scoring'));
    } else {
        if (state.final_turn) {
            turnDiv.innerText = `LAST TURN: Blue`;
            msgDiv.innerText = "Blue gets one final chance!";
        } else {
            // Updated: Show simplistic turn status here
            turnDiv.innerText = `Turn: ${state.current_player}`;
            msgDiv.innerText = `Round ${(Math.floor(state.turn_index / 2) + 1)} / ${state.max_rounds}`;
        }
    }

    // Update Pieces Left
    // Turn Index counts COMPLETED moves (starts at 0).
    // Red moves = ceil(turn_index / 2)
    // Blue moves = floor(turn_index / 2)
    const redPlayed = Math.ceil(state.turn_index / 2);
    const bluePlayed = Math.floor(state.turn_index / 2);

    const maxRounds = state.max_rounds || 25; // Default to 25 if undefined

    document.getElementById('pieces-red').innerText = `Pieces: ${Math.max(0, maxRounds - redPlayed)}`;
    document.getElementById('pieces-blue').innerText = `Pieces: ${Math.max(0, maxRounds - bluePlayed)}`;
}

/**
 * Counts up the number from 'start' to 'end' visually.
 * Also shows a fleeting popup if points increased.
 */
function animateScore(elementId, start, end, cardId) {
    if (start === end) return;

    const element = document.getElementById(elementId);

    // Show "+Points" popup on the card
    const diff = end - start;
    if (diff > 0) {
        const popup = document.createElement('div');
        popup.className = 'score-popup';
        popup.innerText = `+${diff}`;
        document.getElementById(cardId).appendChild(popup);
        setTimeout(() => popup.remove(), 1000);
    }

    // Number roll animation
    let current = start;
    // Calculate speed: faster for larger jumps
    const stepTime = Math.max(10, 500 / (diff || 1));

    const timer = setInterval(() => {
        current += 1;
        if (current > end) current = end;
        element.innerText = current;
        if (current >= end) {
            clearInterval(timer);
        }
    }, stepTime);
}

// --------------------------------------------------------------------------
// Hexagon Math & Drawing
// --------------------------------------------------------------------------

/**
 * Converts Axial Coordinates (q, r) to Pixel Coordinates (x, y).
 * Math Source: https://www.redblobgames.com/grids/hexagons/#hex-to-pixel
 */
function hexToPixel(q, r) {
    var x = HEX_SIZE * (3 / 2 * q);
    var y = HEX_SIZE * (Math.sqrt(3) / 2 * q + Math.sqrt(3) * r);
    return { x: x + CENTER_X, y: y + CENTER_Y }; // Offset to center of screen
}

/**
 * Redraws the entire SVG grid based on the board state.
 * Optimized to re-use DOM nodes? No, we simply clear and rebuild for simplicity here.
 */
function renderBoard(state) {
    const svg = document.getElementById('hex-grid');
    svg.innerHTML = ''; // Wipe clean

    const board = state.board;

    for (const key in board) {
        // key is "q,r,s" 
        const parts = key.split(',');
        const q = parseInt(parts[0]);
        const r = parseInt(parts[1]);
        const marker = board[key]; // 'Red', 'Blue', or null
        const bonus = state.bonuses ? state.bonuses[key] : null;

        const center = hexToPixel(q, r);
        drawHex(svg, center.x, center.y, q, r, marker, bonus);
    }
}

/**
 * Creates a single Polygon element and appends it to the SVG.
 */
function drawHex(svg, x, y, q, r, marker, bonusMultiplier) {
    // Generate the 6 points of the hexagon
    const points = [];
    for (let i = 0; i < 6; i++) {
        const angle_deg = 60 * i;
        const angle_rad = Math.PI / 180 * angle_deg;
        const px = x + HEX_SIZE * Math.cos(angle_rad);
        const py = y + HEX_SIZE * Math.sin(angle_rad);
        points.push(`${px},${py}`);
    }

    const poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    poly.setAttribute("points", points.join(" "));

    // Store coordinate in data attribute so we can find it later (e.g. for animations)
    poly.setAttribute("data-key", `${q},${r}`);

    // Apply CSS classes based on state
    let classes = "";
    if (marker === 'Red') {
        classes = "hex-marker-red occupied";
    } else if (marker === 'Blue') {
        classes = "hex-marker-blue occupied";
    }

    if (bonusMultiplier && bonusMultiplier > 1) {
        classes += " hex-bonus";
    }

    poly.setAttribute("class", classes.trim());

    // Attach Click Handler
    poly.onclick = () => onHexClick(q, r);
    svg.appendChild(poly);
}

function onHexClick(q, r) {
    if (currentState.game_over || isAnimating) return;

    // Prevent clicking during AI's turn
    if (aiEnabled && currentState.current_player === 'Blue') return;

    // Call Python function
    if (window.py_move) {
        const stateRaw = window.py_move(q, r);
        if (stateRaw) {
            handleStateUpdate(JSON.parse(stateRaw));
        }
    }
}

// --------------------------------------------------------------------------
// Score Log Logic
// --------------------------------------------------------------------------
function toggleLog(player) {
    const container = document.getElementById(`log-container-${player}`);
    const content = document.getElementById(`log-content-${player}`);

    container.classList.toggle('active');
    content.classList.toggle('hidden');
}

function updateScoreLog(player, shapes) {
    const list = document.getElementById(`score-log-list-${player}`);
    if (!list) return;

    list.innerHTML = ''; // Clear existing list

    if (!shapes || shapes.length === 0) {
        const empty = document.createElement('li');
        empty.className = 'score-log-empty';
        empty.innerText = "No scoring shapes.";
        list.appendChild(empty);
        return;
    }

    shapes.forEach(shape => {
        const li = document.createElement('li');
        const name = formatShapeName(shape);
        li.innerHTML = `${name} <strong>(+${shape.points})</strong>`;
        list.appendChild(li);
    });
}

function formatShapeName(shape) {
    const type = shape.type;
    const count = shape.cells.length;

    if (type === 'line') {
        return `Line of ${count}`;
    } else if (type === 'loop') {
        return `Loop`;
    } else if (type.startsWith('triangle')) {
        const size = type.split('_')[1];
        return `Triangle (Size ${size})`;
    } else if (type.startsWith('hollow')) {
        const dim = type.split('_')[1];
        return `Hollow Hex (${dim})`; // e.g. 3x3
    } else if (type === 'variety_bonus') {
        return "Variety Bonus (Jackpot!)";
    }
    return type.charAt(0).toUpperCase() + type.slice(1);
}

/**
 * Shows a temporary toast/popup message on the game board.
 */
function showErrorPopup(message) {
    const container = document.getElementById('game-board');

    // Remove any existing toast to prevent stacking
    const existing = container.querySelector('.game-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'game-toast';
    toast.innerText = message;

    container.appendChild(toast);

    // Automatically removed by CSS animation, but good practice to clean up DOM.
    // CSS animation is 1s total.
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 1000);
}
