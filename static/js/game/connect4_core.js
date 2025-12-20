document.addEventListener("DOMContentLoaded", () => {
  const boardDiv = document.getElementById("board");
  const rows = parseInt(boardDiv.dataset.rows, 10);
  const cols = parseInt(boardDiv.dataset.cols, 10);

  const statusDiv = document.getElementById("status");
  const resetBtn = document.getElementById("resetBtn");
  const columnButtons = Array.from(document.querySelectorAll(".column-header"));
  const thinkingIndicator = document.getElementById("thinkingIndicator");

  const humanAvatar = document.getElementById("humanAvatar");
  const aiAvatar = document.getElementById("aiAvatar");

  const aiModeSelect = document.getElementById("aiModeSelect");
  const modeBadge = document.getElementById("modeBadge");

  let gameOver = false;
  let isWaiting = false;
  let isPlayerTurn = true;

  const THINK_DELAY_MS = 700;

  function getSelectedMode() {
    if (!aiModeSelect) return "minimax";
    const v = (aiModeSelect.value || "minimax").toLowerCase();
    return v === "mcts" ? "mcts" : "minimax";
  }

  function setModeBadge(mode) {
    if (!modeBadge) return;
    const label = mode === "mcts" ? "MCTS" : "Minimax";
    modeBadge.textContent = `Mode: ${label}`;
  }

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
        cell.className = "cell";
        if (value === 0) cell.classList.add("empty");
        else if (value === 1) cell.classList.add("player");
        else if (value === 2) cell.classList.add("ai");
      }
    }
  }

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

    // optimistic UI
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

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const msg = data.error || data.details || "Server error.";
        statusDiv.textContent = msg;
        showThinking(false);
        isWaiting = false;
        isPlayerTurn = true;
        setActiveAvatar("human");
        return;
      }

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

          if (data.redirect_to_report) {
            setTimeout(() => {
              window.location.href = data.redirect_to_report;
            }, 1200);
          }
        }

        isWaiting = false;
      }, THINK_DELAY_MS);
    } catch (err) {
      console.error(err);
      statusDiv.textContent = "Network error (couldn't reach server).";
      showThinking(false);
      isWaiting = false;
      isPlayerTurn = true;
      setActiveAvatar("human");
    }
  }

  async function resetGame() {
    const mode = getSelectedMode();
    setModeBadge(mode);

    // ✅ Don't permanently disable the dropdown.
    // Only disable while the "new game" request is in-flight.
    if (aiModeSelect) aiModeSelect.disabled = true;

    try {
      const response = await fetch("/api/connect4/new", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ai_mode: mode }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        statusDiv.textContent = data.error || "Could not start a new game.";
        if (aiModeSelect) aiModeSelect.disabled = false;
        return;
      }

      renderBoard(data.board);
      gameOver = false;
      isWaiting = false;
      isPlayerTurn = true;
      showThinking(false);
      setActiveAvatar("human");

      // server may confirm selected mode
      if (data.ai_mode) setModeBadge(data.ai_mode);

      statusDiv.textContent = "New game started. Your turn!";
    } catch (err) {
      console.error(err);
      statusDiv.textContent = "Could not start a new game (network error).";
    } finally {
      // ✅ re-enable dropdown after reset finishes
      if (aiModeSelect) aiModeSelect.disabled = false;
    }
  }

  // listeners
  columnButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const col = parseInt(btn.dataset.col, 10);
      makeMove(col);
    });
  });

  resetBtn.addEventListener("click", () => {
    resetGame();
  });

  // ✅ If user changes mode, start a fresh game in that mode
  if (aiModeSelect) {
    aiModeSelect.addEventListener("change", () => {
      resetGame();
    });
  }

  // init
  resetGame();
});
