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


  function setWall(r, c) {
  const isStart = startCell && startCell[0] === r && startCell[1] === c;
  const isGoal = goalCell && goalCell[0] === r && goalCell[1] === c;
  if (!isStart && !isGoal) setCell(r, c, 1);
}

function carve(r, c) {
  const isStart = startCell && startCell[0] === r && startCell[1] === c;
  const isGoal = goalCell && goalCell[0] === r && goalCell[1] === c;
  if (!isStart && !isGoal) setCell(r, c, 0);
}

function randInt(a, b) {
  return Math.floor(Math.random() * (b - a + 1)) + a;
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

    else if (type === "wave") {
  // Clean base
  clearNonSpecialCells();

  // Build a sine-like thick wall line across the grid
  const amplitude = Math.floor(rows * 0.35);
  const mid = Math.floor(rows / 2);
  const thickness = 2;

  for (let c = 0; c < cols; c++) {
    const t = (c / cols) * (Math.PI * 2.2); // number of waves
    const rCenter = mid + Math.round(Math.sin(t) * amplitude);

    for (let dr = -thickness; dr <= thickness; dr++) {
      const rr = rCenter + dr;
      if (rr > 0 && rr < rows - 1) setWall(rr, c);
    }
  }

  runStatus.textContent = "Wave walls generated. Great for A* vs BFS comparison.";
}

else if (type === "spiral") {
  clearNonSpecialCells();

  // Fill all as walls first
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const isStart = startCell && startCell[0] === r && startCell[1] === c;
      const isGoal = goalCell && goalCell[0] === r && goalCell[1] === c;
      if (!isStart && !isGoal) setCell(r, c, 1);
    }
  }

  // Carve spiral corridor
  let top = 1, left = 1;
  let bottom = rows - 2, right = cols - 2;

  while (top <= bottom && left <= right) {
    for (let c = left; c <= right; c++) carve(top, c);
    top += 2;

    for (let r = top; r <= bottom; r++) carve(r, right);
    right -= 2;

    if (top <= bottom) {
      for (let c = right; c >= left; c--) carve(bottom, c);
      bottom -= 2;
    }

    if (left <= right) {
      for (let r = bottom; r >= top; r--) carve(r, left);
      left += 2;
    }
  }

  runStatus.textContent = "Spiral maze generated.";
}

else if (type === "division") {
  clearNonSpecialCells();

  // Start with empty grid; add border walls
  for (let r = 0; r < rows; r++) {
    setWall(r, 0);
    setWall(r, cols - 1);
  }
  for (let c = 0; c < cols; c++) {
    setWall(0, c);
    setWall(rows - 1, c);
  }

  function divide(x, y, w, h) {
    if (w < 6 || h < 6) return;

    const horizontal = w < h; // choose cut direction
    if (horizontal) {
      const wallY = y + (randInt(1, Math.floor((h - 2) / 2)) * 2);
      const holeX = x + (randInt(0, Math.floor((w - 2) / 2)) * 2 + 1);

      for (let cx = x; cx < x + w; cx++) {
        if (cx !== holeX) setWall(wallY, cx);
      }

      divide(x, y, w, wallY - y);
      divide(x, wallY + 1, w, y + h - (wallY + 1));
    } else {
      const wallX = x + (randInt(1, Math.floor((w - 2) / 2)) * 2);
      const holeY = y + (randInt(0, Math.floor((h - 2) / 2)) * 2 + 1);

      for (let ry = y; ry < y + h; ry++) {
        if (ry !== holeY) setWall(ry, wallX);
      }

      divide(x, y, wallX - x, h);
      divide(wallX + 1, y, x + w - (wallX + 1), h);
    }
  }

  divide(1, 1, cols - 2, rows - 2);
  runStatus.textContent = "Recursive division maze generated.";
}

else if (type === "binary") {
  clearNonSpecialCells();

  // Fill walls on all odd cells (classic maze grid)
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) setWall(r, c);
  }

  // Carve cells at odd coordinates
  for (let r = 1; r < rows - 1; r += 2) {
    for (let c = 1; c < cols - 1; c += 2) {
      carve(r, c);

      const carveUp = Math.random() < 0.5;
      if (carveUp && r - 1 > 0) carve(r - 1, c);
      else if (c + 1 < cols - 1) carve(r, c + 1);
    }
  }

  runStatus.textContent = "Binary Tree maze generated.";
}

else if (type === "sidewinder") {
  clearNonSpecialCells();

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) setWall(r, c);
  }

  // Carve odd cells
  for (let r = 1; r < rows - 1; r += 2) {
    let run = [];
    for (let c = 1; c < cols - 1; c += 2) {
      carve(r, c);
      run.push([r, c]);

      const atEast = (c + 2 >= cols - 1);
      const atNorth = (r - 2 <= 0);
      const carveEast = (!atEast && (atNorth || Math.random() < 0.7));

      if (carveEast) {
        carve(r, c + 1);
      } else {
        // carve north from a random cell in run
        const pick = run[randInt(0, run.length - 1)];
        if (pick[0] - 1 > 0) carve(pick[0] - 1, pick[1]);
        run = [];
      }
    }
  }

  runStatus.textContent = "Sidewinder maze generated.";
}

else if (type === "rooms") {
  clearNonSpecialCells();

  // Fill everything with walls
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) setWall(r, c);
  }

  function carveRoom(r0, c0, rh, cw) {
    for (let r = r0; r < r0 + rh; r++) {
      for (let c = c0; c < c0 + cw; c++) {
        if (r > 0 && r < rows - 1 && c > 0 && c < cols - 1) carve(r, c);
      }
    }
  }

  const roomCount = 6;
  const rooms = [];
  for (let i = 0; i < roomCount; i++) {
    const rh = randInt(4, 7);
    const cw = randInt(6, 10);
    const r0 = randInt(1, rows - rh - 2);
    const c0 = randInt(1, cols - cw - 2);
    carveRoom(r0, c0, rh, cw);
    rooms.push([r0 + Math.floor(rh / 2), c0 + Math.floor(cw / 2)]);
  }

  // Connect rooms with corridors
  for (let i = 1; i < rooms.length; i++) {
    const [r1, c1] = rooms[i - 1];
    const [r2, c2] = rooms[i];

    // horizontal then vertical corridor
    const stepC = c1 <= c2 ? 1 : -1;
    for (let c = c1; c !== c2; c += stepC) carve(r1, c);

    const stepR = r1 <= r2 ? 1 : -1;
    for (let r = r1; r !== r2; r += stepR) carve(r, c2);
  }

  runStatus.textContent = "Rooms + corridors generated.";
}


    clearVisualMarks();
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
if (data.run_id) {
  const reportLink = document.getElementById("reportLink");
  if (reportLink) {
    reportLink.href = `/visualizer/report?run_id=${data.run_id}`;
  }
}



/* ================================
   AI AGENT VISUALIZATION REPORT
   ================================ */
if (data.agent_report) {
  const agent = data.agent_report;

  const summaryDiv = document.getElementById("agentSummary");
  const bulletsUl = document.getElementById("agentBullets");

  if (summaryDiv) {
    summaryDiv.textContent = agent.high_level || "";
  }

  if (bulletsUl) {
    bulletsUl.innerHTML = "";
    (agent.bullets || []).slice(0, 12).forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      bulletsUl.appendChild(li);
    });
  }
}

/* ================================ */

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
