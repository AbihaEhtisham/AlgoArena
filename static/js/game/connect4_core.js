document.addEventListener("DOMContentLoaded", () => {
  const boardDiv = document.getElementById("board");
  const rows = parseInt(boardDiv.dataset.rows, 10);
  const cols = parseInt(boardDiv.dataset.cols, 10);

  const statusDiv = document.getElementById("status");
  const resetBtn = document.getElementById("resetBtn");
  const columnButtons = Array.from(
    document.querySelectorAll(".column-header")
  );
  const thinkingIndicator = document.getElementById("thinkingIndicator");

  const humanAvatar = document.getElementById("humanAvatar");
  const aiAvatar = document.getElementById("aiAvatar");

  let gameOver = false;
  let isWaiting = false;
  let isPlayerTurn = true;

  const THINK_DELAY_MS = 800; // delay before showing AI move

  function setActiveAvatar(side) {
    if (!humanAvatar || !aiAvatar) return;
    if (side === "human") {
      humanAvatar.classList.add("active");
      aiAvatar.classList.remove("active");
    } else if (side === "ai") {
      aiAvatar.classList.add("active");
      humanAvatar.classList.remove("active");
    } else {
      humanAvatar.classList.remove("active");
      aiAvatar.classList.remove("active");
    }
  }

  function showThinking(show) {
    if (!thinkingIndicator) return;
    thinkingIndicator.classList.toggle("hidden", !show);
  }

  function renderBoard(board) {
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cell = document.getElementById(`cell-${r}-${c}`);
        const value = board[r][c];
        cell.className = "cell"; // reset base
        if (value === 0) {
          cell.classList.add("empty");
        } else if (value === 1) {
          cell.classList.add("player");
        } else if (value === 2) {
          cell.classList.add("ai");
        }
      }
    }
  }

  // Optimistically drop player's disc in UI (DOM only)
  function dropPlayerDiscUI(column) {
    for (let r = rows - 1; r >= 0; r--) {
      const cell = document.getElementById(`cell-${r}-${column}`);
      if (cell && cell.classList.contains("empty")) {
        cell.classList.remove("empty");
        cell.classList.add("player");
        break;
      }
    }
  }

  async function makeMove(column) {
    if (gameOver || isWaiting || !isPlayerTurn) return;
    isWaiting = true;

    // Optimistic UI: show player's disc immediately
    dropPlayerDiscUI(column);
    statusDiv.textContent = "You played. AI is thinking...";
    setActiveAvatar("ai");
    showThinking(true);
    isPlayerTurn = false;

    try {
      const response = await fetch("/api/connect4/player-move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ column }),
      });

      const data = await response.json();

      if (!response.ok) {
        statusDiv.textContent = data.error || "Error occurred.";
        // In case of server error, force a board refresh via new game
        showThinking(false);
        isWaiting = false;
        return;
      }

      // Wait a bit so the user SEES "AI thinking"
      setTimeout(() => {
        renderBoard(data.board);

        if (data.status === "ongoing") {
          statusDiv.textContent = "Your turn. Click a column.";
          showThinking(false);
          setActiveAvatar("human");
          isPlayerTurn = true;
          gameOver = false;
        } else {
          gameOver = true;
          showThinking(false);

          if (data.winner === "player") {
            statusDiv.textContent =
              "You win! Redirecting to AI progress report...";
          } else if (data.winner === "ai") {
            statusDiv.textContent =
              "AI wins! Redirecting to AI progress report...";
          } else {
            statusDiv.textContent =
              "It's a draw. Redirecting to AI progress report...";
          }

          // Redirect to server-side report page
          if (data.redirect_to_report) {
            setTimeout(() => {
              window.location.href = data.redirect_to_report;
            }, 1500);
          }
        }

        isWaiting = false;
      }, THINK_DELAY_MS);
    } catch (err) {
      console.error(err);
      statusDiv.textContent = "Network error.";
      showThinking(false);
      isWaiting = false;
      isPlayerTurn = true;
      setActiveAvatar("human");
    }
  }

  async function resetGame() {
    try {
      const response = await fetch("/api/connect4/new", {
        method: "POST",
      });
      const data = await response.json();
      renderBoard(data.board);
      gameOver = false;
      isWaiting = false;
      isPlayerTurn = true;
      showThinking(false);
      setActiveAvatar("human");
      statusDiv.textContent = "New game started. Your turn!";
    } catch (err) {
      console.error(err);
      statusDiv.textContent = "Could not start a new game.";
    }
  }

  // Attach listeners
  columnButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const col = parseInt(btn.dataset.col, 10);
      makeMove(col);
    });
  });

  resetBtn.addEventListener("click", () => {
    resetGame();
  });

  // Initialize a new game on first load
  resetGame();
});
