const HEX_SIZE = 25;
const BOARD_RADIUS = 4;
const VIEW_WIDTH = 600;
const VIEW_HEIGHT = 600;
const CENTER_X = VIEW_WIDTH / 2;
const CENTER_Y = VIEW_HEIGHT / 2;

let currentState = null;
let aiEnabled = false;
let previousScores = { 'Red': 0, 'Blue': 0 };
let isAnimating = false;

window.setAiEnabled = function (val) {
    aiEnabled = val;
}

document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch, but we might want to prompt new game immediately
    // fetchState(); 

    // Show modal by default on load
    showModal();

    document.getElementById('open-new-game-btn').addEventListener('click', () => {
        showModal();
    });

    // document.getElementById('start-game-btn').addEventListener('click', () => {
    //      // Managed by PyScript @when('click', '#start-game-btn')
    // });

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



function handleStateUpdate(state) {
    if (state.error) {
        console.error(state.error);
        return;
    }

    // If we are currently animating, we might want to queue this update? 
    // Or simpler: The backend state is the truth. 
    // If there is a scoring event, we want to animate it BEFORE showing the final state fully?
    // Or just run the animation sequence which essentially decorates the board.

    const oldState = currentState;
    currentState = state;

    // Render basic board (markers) immediately, but WITHOUT scoring highlights
    renderBoard(state);

    // Note: detailed scoring animation needs to know about the LAST move's shapes.
    // If this update comes from an API call that resulted in scoring, `last_scoring_event` will be populated.

    if (state.last_turn_shapes) {
        updateScoreLog('red', state.last_turn_shapes.Red);
        updateScoreLog('blue', state.last_turn_shapes.Blue);
    }

    if (state.last_scoring_event && state.last_scoring_event.length > 0) {
        animateScoringSequence(state.last_scoring_event, state);
    } else {
        // Just update UI immediately
        updateUI(state);
        // If Game Over, ensure we clear any lingering highlights (handled by renderBoard not adding them)
        if (state.game_over) {
            // No special action needed if we don't persist highlights
        }
        checkAiTurn();
    }
}

async function animateScoringSequence(shapes, state) {
    isAnimating = true;

    // Queue of animations
    for (const shape of shapes) {
        // 1. Highlight Hexes
        const shapeCells = shape.cells.map(c => `${c.q},${c.r}`);
        highlightHexes(shapeCells, true);

        // 2. Show Label
        const center = calculateShapeCenter(shape.cells);
        showShapeLabel(center, `+${shape.points}`);

        // 3. Update Scoreboard partially? 
        // For simplicity, we just animate the full score jump at the end or locally?
        // User asked: "show each score in succession".
        // Use a local accumulator or just let the score animation run?
        // Let's just pause to let the user see the shape.
        await wait(800);

        // 4. Cleanup this shape
        highlightHexes(shapeCells, false);
        // Label removes itself via CSS animation usually, or we clean it
        removeShapeLabels();

        await wait(200);
    }

    isAnimating = false;
    updateUI(state); // Update final scores and text
    checkAiTurn();
}

function highlightHexes(cellKeys, active) {
    const svg = document.getElementById('hex-grid');
    // Map keys "q,r" to elements.
    // We didn't store a map. Select by data attribute? 
    // We re-rendered board. Let's add data attributes to polys in renderBoard.

    cellKeys.forEach(k => {
        const poly = svg.querySelector(`polygon[data-key="${k}"]`);
        if (poly) {
            if (active) poly.classList.add('hex-scoring');
            else poly.classList.remove('hex-scoring');
        }
    });
}

function showShapeLabel(pos, text) {
    const container = document.getElementById('game-board');
    const label = document.createElement('div');
    label.className = 'shape-score-label';
    label.innerText = text;
    // Position
    label.style.left = `${pos.x}px`;
    label.style.top = `${pos.y}px`;

    container.appendChild(label);
}

function removeShapeLabels() {
    const container = document.getElementById('game-board');
    const labels = container.querySelectorAll('.shape-score-label');
    labels.forEach(l => l.remove());
}

function calculateShapeCenter(cells) {
    let sumX = 0, sumY = 0;
    cells.forEach(c => {
        const p = hexToPixel(c.q, c.r);
        sumX += p.x;
        sumY += p.y;
    });
    return { x: sumX / cells.length, y: sumY / cells.length };
}

function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function checkAiTurn() {
    if (aiEnabled && currentState && currentState.current_player === 'Blue' && !currentState.game_over && !isAnimating) {
        setTimeout(() => {
            if (window.py_ai_move) {
                const stateRaw = window.py_ai_move();
                if (stateRaw) {
                    handleStateUpdate(JSON.parse(stateRaw));
                }
            }
        }, 500);
    }
}

function updateUI(state) {
    // Animate scores
    animateScore('score-red', previousScores['Red'], state.scores['Red'], 'card-red');
    animateScore('score-blue', previousScores['Blue'], state.scores['Blue'], 'card-blue');

    previousScores = { ...state.scores };

    // Update Last Turn Scores
    if (state.last_turn_points) {
        document.getElementById('last-turn-red').innerText = `Last Turn: ${state.last_turn_points['Red']}`;
        document.getElementById('last-turn-blue').innerText = `Last Turn: ${state.last_turn_points['Blue']}`;
    }

    const turnDiv = document.getElementById('turn-indicator');
    const msgDiv = document.getElementById('message-area');

    // Update Active Turn Card
    document.getElementById('card-red').classList.toggle('active-turn', state.current_player === 'Red' && !state.game_over);
    document.getElementById('card-blue').classList.toggle('active-turn', state.current_player === 'Blue' && !state.game_over);

    // Update body class for hover effects
    document.body.className = '';
    if (!state.game_over && !isAnimating) {
        document.body.classList.add(state.current_player === 'Red' ? 'turn-red' : 'turn-blue');
    }

    if (state.game_over) {
        turnDiv.innerText = "Game Over!";
        msgDiv.innerText = `Winner: ${state.winner}`;
        // Un-highlight everything just in case
        // Actually highlightHexes requires keys. 
        // Just clear all.
        document.querySelectorAll('.hex-scoring').forEach(el => el.classList.remove('hex-scoring'));
    } else {
        if (state.final_turn) {
            turnDiv.innerText = `LAST TURN: Blue`;
            msgDiv.innerText = "Blue gets one final chance!";
        } else {
            turnDiv.innerText = `Turn: ${state.current_player}`;
            msgDiv.innerText = "";
        }
    }
}

function animateScore(elementId, start, end, cardId) {
    if (start === end) return;

    const element = document.getElementById(elementId);

    // Floating popup handled by shape labels now? 
    // Maybe keep this for total sum update feedback?
    // User asked "Show point value of *each* scoring formation over the hexes".
    // We did that. 
    // We can keep the card popup as a "total added" indicator or remove it to reduce noise.
    // Let's keep it but simpler.

    const diff = end - start;
    if (diff > 0) {
        // Floating popup on card
        const popup = document.createElement('div');
        popup.className = 'score-popup';
        popup.innerText = `+${diff}`;
        document.getElementById(cardId).appendChild(popup);
        setTimeout(() => popup.remove(), 1000);
    }

    // Count up animation
    let current = start;
    const stepTime = Math.max(10, 500 / (diff || 1));

    const timer = setInterval(() => {
        current += 1;
        if (current > end) current = end; // Safety
        element.innerText = current;
        if (current >= end) {
            clearInterval(timer);
        }
    }, stepTime);
}

function hexToPixel(q, r) {
    var x = HEX_SIZE * (3 / 2 * q);
    var y = HEX_SIZE * (Math.sqrt(3) / 2 * q + Math.sqrt(3) * r);
    return { x: x + CENTER_X, y: y + CENTER_Y };
}

function renderBoard(state) {
    const svg = document.getElementById('hex-grid');
    svg.innerHTML = '';

    const board = state.board;

    // We no longer persist scoring highlights here. 
    // Only markers.

    for (const key in board) {
        const parts = key.split(',');
        const q = parseInt(parts[0]);
        const r = parseInt(parts[1]);
        const marker = board[key];

        const center = hexToPixel(q, r);
        drawHex(svg, center.x, center.y, q, r, marker);
    }
}

function drawHex(svg, x, y, q, r, marker) {
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

    // Store data-key for animation lookups
    poly.setAttribute("data-key", `${q},${r}`);

    if (marker === 'Red') {
        poly.setAttribute("class", "hex-marker-red occupied");
    } else if (marker === 'Blue') {
        poly.setAttribute("class", "hex-marker-blue occupied");
    } else {
        poly.setAttribute("class", "");
    }

    poly.onclick = () => onHexClick(q, r);
    svg.appendChild(poly);
}

function onHexClick(q, r) {
    if (currentState.game_over || isAnimating) return;
    if (aiEnabled && currentState.current_player === 'Blue') return;

    // PyScript call
    if (window.py_move) {
        const stateRaw = window.py_move(q, r);
        if (stateRaw) {
            handleStateUpdate(JSON.parse(stateRaw));
        }
    }
}



function toggleLog(player) {
    const container = document.getElementById(`log-container-${player}`);
    const content = document.getElementById(`log-content-${player}`);

    container.classList.toggle('active');
    content.classList.toggle('hidden');
}

function updateScoreLog(player, shapes) {
    const list = document.getElementById(`score-log-list-${player}`);
    if (!list) return;

    list.innerHTML = ''; // Clear existing

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
    }

    // Fallback
    return type.charAt(0).toUpperCase() + type.slice(1);
}
