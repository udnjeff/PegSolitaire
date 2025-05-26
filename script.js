// Global Variables
let board = [
    [-1, -1, 1, 1, 1, -1, -1],
    [-1, -1, 1, 1, 1, -1, -1],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [-1, -1, 1, 1, 1, -1, -1],
    [-1, -1, 1, 1, 1, -1, -1]
];
let selectedPeg = null;
let history = [];
let redoStack = [];
let moveHistory = [];
let redoMoveHistoryStack = []; // For storing move strings during undo
const initialBoardState = [ // Define initial board state for newGame and undoAll
    [-1, -1, 1, 1, 1, -1, -1],
    [-1, -1, 1, 1, 1, -1, -1],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [-1, -1, 1, 1, 1, -1, -1],
    [-1, -1, 1, 1, 1, -1, -1]
];
const pegSize = 40; // Not directly used for rendering, CSS handles it.
const boardPadding = 20; // Not directly used for rendering.

// DOM Element References
const gameBoardDiv = document.getElementById('game-board');
const cells = []; // Will be populated with references to cell divs
for (let r = 0; r < 7; r++) {
    for (let c = 0; c < 7; c++) {
        cells.push(document.getElementById(`cell-${r}-${c}`));
    }
}

const newGameBtn = document.getElementById('new-game-btn');
const undoAllBtn = document.getElementById('undo-all-btn');
const undoBtn = document.getElementById('undo-btn');
const redoBtn = document.getElementById('redo-btn');
const redoAllBtn = document.getElementById('redo-all-btn');
const moveHistoryTextarea = document.getElementById('move-history');

// drawBoard() Function
function drawBoard() {
    for (let r = 0; r < 7; r++) {
        for (let c = 0; c < 7; c++) {
            const cellDiv = document.getElementById(`cell-${r}-${c}`);
            // Skip off-board cells for peg/empty/selected logic, but ensure they don't get other classes
            if (board[r][c] === -1) {
                cellDiv.classList.remove('peg', 'empty', 'selected-peg');
                continue;
            }

            cellDiv.classList.remove('peg', 'empty', 'selected-peg');

            if (board[r][c] === 1) {
                cellDiv.classList.add('peg');
                if (selectedPeg && selectedPeg.row === r && selectedPeg.col === c) {
                    cellDiv.classList.add('selected-peg');
                }
            } else if (board[r][c] === 0) {
                cellDiv.classList.add('empty');
            }
        }
    }
}

// getCellFromPos(event) - simplified by parsing ID in onClick
// No separate function needed if parsing ID directly in onClick

// onClick(event) Function
function onClick(event) {
    const clickedCellId = event.target.id;
    if (!clickedCellId || !clickedCellId.startsWith('cell-')) {
        return; // Clicked outside a cell or on a non-cell element
    }

    const parts = clickedCellId.split('-');
    const row = parseInt(parts[1]);
    const col = parseInt(parts[2]);

    if (board[row][col] === -1) { // Clicked an off-board cell
        return;
    }

    if (selectedPeg === null) {
        if (board[row][col] === 1) { // Clicked on a peg
            selectedPeg = { row, col };
        }
    } else { // A peg is already selected
        const fromRow = selectedPeg.row;
        const fromCol = selectedPeg.col;
        const toRow = row;
        const toCol = col;

        let moveSuccessful = makeMove(fromRow, fromCol, toRow, toCol);

        if (moveSuccessful) {
            selectedPeg = null;
            // drawBoard(); // Already called at the end of onClick
            checkGameOver(); // Add this call
        } else {
            // If the move was not successful:
            // If the clicked cell is another peg, select it.
            // Otherwise (clicked an empty cell that's not a valid move, or the same peg), deselect.
            if (board[toRow][toCol] === 1) {
                selectedPeg = { row: toRow, col: toCol }; // Select the new peg
            } else {
                selectedPeg = null; // Deselect
            }
        }
    }
    drawBoard();
}

// isValidMove Function
function isValidMove(fromRow, fromCol, toRow, toCol) {
    // Check bounds
    if (fromRow < 0 || fromRow > 6 || fromCol < 0 || fromCol > 6 ||
        toRow < 0 || toRow > 6 || toCol < 0 || toCol > 6) {
        return false;
    }

    // Check if starting position has a peg and target is empty
    if (board[fromRow][fromCol] !== 1 || board[toRow][toCol] !== 0) {
        return false;
    }

    // Check for 2-space horizontal jump
    if (Math.abs(fromRow - toRow) === 0 && Math.abs(fromCol - toCol) === 2) {
        const jumpedCol = (fromCol + toCol) / 2;
        if (board[fromRow][jumpedCol] === 1) {
            return true;
        }
    }

    // Check for 2-space vertical jump
    if (Math.abs(fromRow - toRow) === 2 && Math.abs(fromCol - toCol) === 0) {
        const jumpedRow = (fromRow + toRow) / 2;
        if (board[jumpedRow][fromCol] === 1) {
            return true;
        }
    }

    return false;
}

// makeMove Function
function makeMove(fromRow, fromCol, toRow, toCol) {
    if (!isValidMove(fromRow, fromCol, toRow, toCol)) {
        return false;
    }

    // Save current state for undo
    history.push(JSON.parse(JSON.stringify(board)));
    redoStack = []; // Clear redo stack on new move

    // Record move string
    moveHistory.push(formatMove(fromRow, fromCol, toRow, toCol));

    // Update board state
    board[fromRow][fromCol] = 0; // Remove peg from original position
    board[toRow][toCol] = 1;     // Place peg at new position

    // Remove the jumped peg
    if (Math.abs(fromRow - toRow) === 2) { // Vertical jump
        board[(fromRow + toRow) / 2][fromCol] = 0;
    } else if (Math.abs(fromCol - toCol) === 2) { // Horizontal jump
        board[fromRow][(fromCol + toCol) / 2] = 0;
    }

    updateHistoryDisplay();
    // checkGameOver() is now called from onClick after a successful move
    return true;
}

// formatMove Function
function formatMove(fromRow, fromCol, toRow, toCol) {
    const fromColChar = String.fromCharCode(65 + fromCol);
    const fromRowNumber = fromRow + 1;
    // The 'to' in the problem description refers to the landing spot of the peg.
    // The "over" implies jumping over a peg that was between 'from' and 'to'.
    // The Python version's output example "C4 over E4" implies 'E4' is the destination.
    const toColChar = String.fromCharCode(65 + toCol);
    const toRowNumber = toRow + 1;

    // Let's clarify the "over" part. The instruction says:
    // "Return a string in the format: fromColChar + fromRowNumber + " over " + toColChar + toRowNumber"
    // This seems to mean the peg *lands* at toColChar, toRowNumber.
    // The Python example `game.make_move(3, 2, 3, 4)` with output "Peg from (3,2) to (3,4)"
    // maps to from (C4) to (E4). The text for this should be "C4 to E4" or "C4 jumps to E4".
    // If "over" is used, it should refer to the peg being jumped.
    // Let's assume the problem meant the start and end points of the *moving* peg.
    // So, "C4 to E4" would be more accurate if (3,2) is C4 and (3,4) is E4.

    // Re-reading: "fromColChar + fromRowNumber + " over " + toColChar + toRowNumber"
    // This is ambiguous. Let's use "from X to Y" for clarity of the peg's movement.
    // If "over" must be used, it implies the jumped peg.
    // Let's stick to the requested format literally, interpreting 'to' as the landing square.
    return `${fromColChar}${fromRowNumber} over ${toColChar}${toRowNumber}`;
}

// updateHistoryDisplay Function
function updateHistoryDisplay() {
    moveHistoryTextarea.value = ""; // Clear existing content
    moveHistory.forEach((moveStr, index) => {
        moveHistoryTextarea.value += `${index + 1}. ${moveStr}\n`;
    });
}


// Initial Call & Event Listeners
drawBoard(); // Draw the initial board

cells.forEach(cellDiv => {
    if (cellDiv && !cellDiv.classList.contains('off-board')) {
        cellDiv.addEventListener('click', onClick);
    }
});

// --- New Game Function ---
function newGame() {
    board = JSON.parse(JSON.stringify(initialBoardState));
    history = [];
    redoStack = [];
    moveHistory = [];
    redoMoveHistoryStack = [];
    selectedPeg = null;
    updateHistoryDisplay();
    drawBoard();
}

// --- Undo Function ---
function undo() {
    if (history.length === 0) {
        alert("Cannot undo!");
        return;
    }
    // Save current board to redoStack
    redoStack.push(JSON.parse(JSON.stringify(board)));
    // Restore previous board from history
    board = history.pop();

    // Move corresponding move string to redoMoveHistoryStack
    if (moveHistory.length > 0) {
        redoMoveHistoryStack.push(moveHistory.pop());
    }

    selectedPeg = null;
    updateHistoryDisplay();
    drawBoard();
}

// --- Redo Function ---
function redo() {
    if (redoStack.length === 0) {
        alert("Cannot redo!");
        return;
    }
    // Save current board to history
    history.push(JSON.parse(JSON.stringify(board)));
    // Restore board from redoStack
    board = redoStack.pop();

    // Move corresponding move string from redoMoveHistoryStack back to moveHistory
    if (redoMoveHistoryStack.length > 0) {
        moveHistory.push(redoMoveHistoryStack.pop());
    }

    selectedPeg = null;
    updateHistoryDisplay();
    drawBoard();
}

// --- Undo All Function ---
function undoAll() {
    if (history.length === 0) {
        return;
    }

    // Prepare redoStack: current board + all history boards
    redoStack = [JSON.parse(JSON.stringify(board)), ...history.map(b => JSON.parse(JSON.stringify(b)))].reverse();
    // Prepare redoMoveHistoryStack: all moveHistory strings, reversed
    redoMoveHistoryStack = [...moveHistory].reverse();


    // Reset to initial state
    board = JSON.parse(JSON.stringify(initialBoardState));
    history = [];
    moveHistory = [];
    selectedPeg = null;

    updateHistoryDisplay();
    drawBoard();
}

// --- Redo All Function ---
function redoAll() {
    if (redoStack.length === 0) {
        return;
    }

    // The last state in redoStack is the one we want to be on.
    // All states in redoStack (except the last one, which becomes current) go into history.
    // The current board (before redoAll) also needs to be added to history.

    // Save current board (before redoAll) to history
    history.push(JSON.parse(JSON.stringify(board)));
    // Add all but the last state from redoStack to history
    for(let i = 0; i < redoStack.length -1; i++) {
        history.push(JSON.parse(JSON.stringify(redoStack[i])));
    }

    // Set board to the last state in redoStack
    board = JSON.parse(JSON.stringify(redoStack[redoStack.length - 1]));

    // Restore move history
    moveHistory.push(...[...redoMoveHistoryStack].reverse());


    redoStack = [];
    redoMoveHistoryStack = [];
    selectedPeg = null;

    updateHistoryDisplay();
    drawBoard();
}


// --- Attach Event Listeners for Controls ---
newGameBtn.addEventListener('click', newGame);
undoBtn.addEventListener('click', undo);
redoBtn.addEventListener('click', redo);
undoAllBtn.addEventListener('click', undoAll);
redoAllBtn.addEventListener('click', redoAll);

// --- Game Over Logic ---

// showWinnerAnimation Function
function showWinnerAnimation() {
    alert("Congratulations! You won!");
}

// checkGameOver Function
function checkGameOver() {
    let pegCount = 0;
    for (let r = 0; r < 7; r++) {
        for (let c = 0; c < 7; c++) {
            if (board[r][c] === 1) {
                pegCount++;
            }
        }
    }

    if (pegCount === 1) {
        showWinnerAnimation();
        return true; // Game is over, player won
    }

    let possibleMoveExists = false;
    outerLoop: // Label for breaking outer loop if a move is found
    for (let r1 = 0; r1 < 7; r1++) {
        for (let c1 = 0; c1 < 7; c1++) {
            if (board[r1][c1] === 1) { // Found a peg
                const directions = [[0, 2], [0, -2], [2, 0], [-2, 0]]; // Jumps of 2 spaces
                for (const dir of directions) {
                    const dr = dir[0]; // Change in row for the target (empty) cell
                    const dc = dir[1]; // Change in col for the target (empty) cell
                    const r2 = r1 + dr; // Target row
                    const c2 = c1 + dc; // Target col

                    // Check bounds for r2, c2 (0-6 for a 7x7 board)
                    if (r2 >= 0 && r2 < 7 && c2 >= 0 && c2 < 7) {
                        // isValidMove checks if board[r1][c1] is a peg,
                        // board[r2][c2] is empty, and the jumped peg exists.
                        if (isValidMove(r1, c1, r2, c2)) {
                            possibleMoveExists = true;
                            break outerLoop; // Found a valid move, no need to check further
                        }
                    }
                }
            }
        }
    }

    if (!possibleMoveExists) {
        alert("No more valid moves. Game Over!");
        return true; // Game is over, no more moves
    }

    return false; // Game is not over yet
}
