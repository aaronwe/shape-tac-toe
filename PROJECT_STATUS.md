# Project Status & Knowledge Base

**Last Updated:** 2026-01-27

## 📌 Project Overview
**Shape Tac Toe** is a browser-based hexagonal strategy board game.
- **Type:** Abstract Strategy / Puzzle Game.
- **Goal:** Users place markers to form geometric shapes (Lines, Loops, Triangles) and score points.
- **Architecture:** Serverless Web Application.
- **Core Technology:** **PyScript** (allows running the Python game engine directly in the browser via WebAssembly).

## 🏗️ Architecture & Implementation
The project separates concerns between a Python-based Game Engine and a standard Web Frontend, bridged by PyScript.

### 1. Python Game Engine (Backend Logic)
These files run inside the browser's Python environment.
- **`hex_grid.py`**:
  - Implements the hexagonal grid system using Cube Coordinates (`q, r, s`).
  - Handles board storage and neighbor lookups.
- **`scorer.py`**:
  - Contains the complex algorithms for shape detection.
  - Identifies patterns like Lines, Loops, Triangles, and Hollow Shapes.
- **`game.py`**:
  - The main state machine.
  - Manages turns, scores, win conditions, and validation.
  - Includes a basic Greedy AI implementation.

### 2. The Bridge
- **`client_game.py`**:
  - The interface layer exposed to JavaScript.
  - Defines functions like `start_new_game`, `move`, and `ai_move`.
  - Converts Python objects to JSON for the frontend.
- **`pyscript.toml`**:
  - Configuration mapping local files to the browser's virtual file system.

### 3. Frontend (UI & Interaction)
- **`index.html`**:
  - Sets up the DOM and loads the PyScript runtime.
  - Contains the SVG container for the board.
- **`static/script.js`**:
  - Handles user input (clicks).
  - Renders the SVG grid dynamically based on game state.
  - Manages UI animations (score rolling, shape highlighting).
- **`static/styles.css`**:
  - styling for the game board, modal, and glassmorphism UI.

## 🚀 Current State
- **Functional**: The game is fully playable in a browser.
- **Deployment**: Currently designed for local execution via `python3 -m http.server` due to CORS requirements for loading local PyScript, or deployment to static hosting (GitHub Pages, Netlify).
- **Recent Focus**:
  - Documentation improvement (making code beginner-friendly).
  - UI/UX polish (Score logs, animations).
  - AI integration (Greedy AI working).

## 📝 Pending / Active Tasks
- **Documentation**: Continuing to add beginner-friendly comments to codebase.
- **Features**: Potential future work on more advanced AI or online multiplayer.
