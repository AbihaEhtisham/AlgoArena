document.addEventListener("DOMContentLoaded", () => {
  const gridDiv = document.getElementById("grid");
  const rows = parseInt(gridDiv.dataset.rows, 10);
  const cols = parseInt(gridDiv.dataset.cols, 10);

  const algorithmSelect = document.getElementById("algorithmSelect");
  const heuristicSelect = document.getElementById("heuristicSelect");
  const runBtn = document.getElementById("runBtn");
  const clearBtn = document.getElementById("clearBtn");
  const runStatus = document.getElementById("runStatus");

  const toolButtons = Array.from(document.querySelectorAll(".tool-btn"));

  const nodesExpandedSpan = document.getElementById("nodesExpanded");
  const pathLengthSpan = document.getElementById("pathLength");
  const foundPathSpan = document.getElementById("foundPath");
  const reportLinkWrapper = document.getElementById("reportLinkWrapper");

  // Maze dropdown
  const mazeDropdownBtn = document.getElementById("mazeDropdownBtn");
  const mazeDropdownMenu = document.getElementById("mazeDropdownMenu");

  // grid[r][c] → 0=empty,1=wall,2=start,3=goal
  let grid = [];
  let startCell = null;
  let goalCell = null;
  let animating = false;
  let currentTool = "wall";

  function initGrid() {
    grid = [];
    gridDiv.innerHTML = "";
    for (let r = 0; r < rows; r++) {
      const rowDiv = document.createElement("div");
      rowDiv.className = "grid-row";

      const rowArr = [];
      for (let c = 0; c < cols; c++) {
        const cellDiv = document.createElement("div");
        cellDiv.className = "grid-cell empty";
        cellDiv.dataset.row = r;
        cellDiv.dataset.col = c;

        cellDiv.addEventListener("mousedown", handleCellClick);
        rowDiv.appendChild(cellDiv);
        rowArr.push(0);
      }
      gridDiv.appendChild(rowDiv);
      grid.push(rowArr);
    }

    startCell = null;
    goalCell = null;
    resetResults();
  }

  function resetResults() {
    nodesExpandedSpan.textContent = "-";
    pathLengthSpan.textContent = "-";
    foundPathSpan.textContent = "-";
    reportLinkWrapper.style.display = "none";
    runStatus.textContent =
      'Click cells to edit the grid, choose an algorithm, then press "Run".';
  }

  function handleCellClick(e) {
    if (animating) return;
    const cell = e.currentTarget;
    const r = parseInt(cell.dataset.row, 10);
    const c = parseInt(cell.dataset.col, 10);

    if (currentTool === "wall") {
      setCell(r, c, 1);
    } else if (currentTool === "erase") {
      // Avoid erasing start/goal state object
      if (startCell && startCell[0] === r && startCell[1] === c) {
        startCell = null;
      }
      if (goalCell && goalCell[0] === r && goalCell[1] === c) {
        goalCell = null;
      }
      setCell(r, c, 0);
    } else if (currentTool === "start") {
      if (startCell) {
        setCell(startCell[0], startCell[1], 0);
      }
      setCell(r, c, 2);
      startCell = [r, c];
    } else if (currentTool === "goal") {
      if (goalCell) {
        setCell(goalCell[0], goalCell[1], 0);
      }
      setCell(r, c, 3);
      goalCell = [r, c];
    }
  }

  function setCell(r, c, value) {
    grid[r][c] = value;
    const cellDiv = getCellDiv(r, c);
    cellDiv.className = "grid-cell"; // reset base
    if (value === 0) {
      cellDiv.classList.add("empty");
    } else if (value === 1) {
      cellDiv.classList.add("wall");
    } else if (value === 2) {
      cellDiv.classList.add("start");
    } else if (value === 3) {
      cellDiv.classList.add("goal");
    }
  }

  function getCellDiv(r, c) {
    return gridDiv.children[r].children[c];
  }

  // Tool button UI
  toolButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      toolButtons.forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      currentTool = btn.dataset.tool;
    });
  });

  // ---------- Algorithm / heuristic interaction ----------

  function updateHeuristicState() {
    const algo = (algorithmSelect.value || "").trim().toLowerCase();
    const needsHeuristic = (
      algo === "astar" ||
      algo === "greedy" ||
      algo === "wastar" ||
      algo === "idastar" ||
      algo === "beam" ||
      algo === "hill" ||
      algo === "rrhill" ||
      algo === "anneal"
    );

    if (!needsHeuristic) {
      heuristicSelect.classList.add("disabled-heuristic");
      heuristicSelect.dataset.locked = "true";
      runStatus.textContent =
        "Note: This algorithm does not use a heuristic (uninformed or cost-based search).";
    } else {
      heuristicSelect.classList.remove("disabled-heuristic");
      heuristicSelect.dataset.locked = "false";
      runStatus.textContent =
      'Click cells to edit the grid, choose an algorithm, then press "Run".';
    }
  }

  algorithmSelect.addEventListener("change", updateHeuristicState);

  // When user tries to interact with heuristic while it's "disabled"
  heuristicSelect.addEventListener("click", (e) => {
    if (heuristicSelect.dataset.locked === "true") {
      e.preventDefault();
      e.stopPropagation();
      runStatus.textContent =
        "No heuristic is used for uninformed searches like BFS/DFS.";
    }
  });

  heuristicSelect.addEventListener("change", (e) => {
    if (heuristicSelect.dataset.locked === "true") {
      e.preventDefault();
      runStatus.textContent =
        "No heuristic is used for uninformed searches like BFS/DFS.";
      // reset value to default
      heuristicSelect.value = "manhattan";
    }
  });

  // ---------- Maze dropdown ----------

  if (mazeDropdownBtn && mazeDropdownMenu) {
    mazeDropdownBtn.addEventListener("click", () => {
      mazeDropdownMenu.classList.toggle("show");
    });

    document.addEventListener("click", (e) => {
      if (
        !mazeDropdownBtn.contains(e.target) &&
        !mazeDropdownMenu.contains(e.target)
      ) {
        mazeDropdownMenu.classList.remove("show");
      }
    });

    const items = Array.from(
      mazeDropdownMenu.querySelectorAll(".dropdown-item")
    );
    items.forEach((item) => {
      item.addEventListener("click", () => {
        const type = item.dataset.maze;
        applyMaze(type);
        mazeDropdownMenu.classList.remove("show");
      });
    });
  }

  function clearNonSpecialCells() {
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const isStart = startCell && startCell[0] === r && startCell[1] === c;
        const isGoal = goalCell && goalCell[0] === r && goalCell[1] === c;
        if (!isStart && !isGoal) {
          setCell(r, c, 0);
        }
      }
    }
  }

  function applyMaze(type) {
    if (animating) return;

    // Ensure we have start/goal; if not, set defaults
    if (!startCell) {
      startCell = [Math.floor(rows / 2), 2];
      setCell(startCell[0], startCell[1], 2);
    }
    if (!goalCell) {
      goalCell = [Math.floor(rows / 2), cols - 3];
      setCell(goalCell[0], goalCell[1], 3);
    }

    // Clear existing walls first
    clearNonSpecialCells();
    clearVisualMarks();

    if (type === "random") {
      const wallProbability = 0.28;
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const isStart =
            startCell && startCell[0] === r && startCell[1] === c;
          const isGoal = goalCell && goalCell[0] === r && goalCell[1] === c;
          if (!isStart && !isGoal) {
            if (Math.random() < wallProbability) {
              setCell(r, c, 1);
            }
          }
        }
      }
      runStatus.textContent =
        "Generated a basic random maze. You can still edit it with the tools.";
    } else if (type === "box") {
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const isEdge = r === 0 || r === rows - 1 || c === 0 || c === cols - 1;
          const isStart =
            startCell && startCell[0] === r && startCell[1] === c;
          const isGoal = goalCell && goalCell[0] === r && goalCell[1] === c;
          if (isEdge && !isStart && !isGoal) {
            setCell(r, c, 1);
          }
        }
      }
      runStatus.textContent =
        "Generated a box maze around the edges. Feel free to add more walls.";
    } else if (type === "stair") {
      const length = Math.min(rows, cols);
      for (let i = 1; i < length - 1; i++) {
        const r = i;
        const c = i;
        const isStart =
          startCell && startCell[0] === r && startCell[1] === c;
        const isGoal = goalCell && goalCell[0] === r && goalCell[1] === c;
        if (!isStart && !isGoal) {
          setCell(r, c, 1);
        }
      }
      runStatus.textContent =
        "Generated a simple stair pattern. Edit or combine it with other walls.";
    } else if (type === "clear") {
      clearNonSpecialCells();
      runStatus.textContent = "Cleared all walls. Start and goal were kept.";
    }

    resetResults();
  }

  // ---------- Running algorithms ----------

  async function runAlgorithm() {
    if (animating) return;

    const algo = algorithmSelect.value;
    const heuristic = heuristicSelect.value;

    if (!startCell || !goalCell) {
      runStatus.textContent = "Please set both a start and a goal cell.";
      return;
    }

    runStatus.textContent = "Running algorithm...";
    animating = true;
    clearVisualMarks();

  try {
    const response = await fetch("/api/visualizer/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        grid,
        start: startCell,
        goal: goalCell,
        algorithm: algo,
        heuristic,
        params: {
          depth_limit: 25,      // used by DLS
          weight: 1.6,          // used by Weighted A*
          beam_width: 5,        // used by Beam Search
          max_steps: 800,       // used by Random Walk / Local Search
          temperature: 1.0,     // Simulated Annealing start temp
          cooling: 0.995        // Simulated Annealing cooling rate
        }
      })  // <-- this brace was missing in your code
    });

      let data = null;
      try {
        data = await response.json();
      } catch (e) {
  // if server didn't return JSON
        data = { ok: false, error: "Server returned a non-JSON error." };
      }

    if (!response.ok || !data.ok) {
      runStatus.textContent =
        (data && data.error)
          ? `Error: ${data.error}`
          : `Error: Server returned status ${response.status}`;
      animating = false;
      return;
    }


      const visited = data.visited_order || [];
      const path = data.path || [];
      const stats = data.stats || {};

      nodesExpandedSpan.textContent = stats.nodes_expanded ?? "-";
      pathLengthSpan.textContent = stats.path_length ?? "-";
      foundPathSpan.textContent = stats.found ? "Yes" : "No";
      reportLinkWrapper.style.display = "block";

      await animateTraversal(visited, path);
      runStatus.textContent = "Done. View the AI report for an explanation.";
    } catch (err) {
      console.error(err);
      runStatus.textContent = "Network error.";
    } finally {
      animating = false;
    }
  }

  function clearVisualMarks() {
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cell = getCellDiv(r, c);
        cell.classList.remove("visited");
        cell.classList.remove("path");
      }
    }
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function animateTraversal(visited, path) {
    // Draw visited nodes
    for (let i = 0; i < visited.length; i++) {
      const [r, c] = visited[i];
      const cell = getCellDiv(r, c);
      const val = grid[r][c];
      if (val === 2 || val === 3) {
        continue;
      }
      cell.classList.add("visited");
      await sleep(15);
    }

    // Draw final path
    for (let i = 0; i < path.length; i++) {
      const [r, c] = path[i];
      const cell = getCellDiv(r, c);
      const val = grid[r][c];
      if (val === 2 || val === 3) {
        continue;
      }
      cell.classList.remove("visited");
      cell.classList.add("path");
      await sleep(30);
    }
  }

  function clearGrid() {
    initGrid();
  }

  runBtn.addEventListener("click", runAlgorithm);
  clearBtn.addEventListener("click", clearGrid);

  // Initialize on load
  initGrid();
  updateHeuristicState();
});
