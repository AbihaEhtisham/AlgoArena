function addMessage(role, text) {
  const chatLog = document.getElementById("chatLog");
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  msg.appendChild(bubble);
  chatLog.appendChild(msg);

  chatLog.scrollTop = chatLog.scrollHeight;
}

async function sendMessage(text) {
  const status = document.getElementById("tutorStatus");
  status.textContent = "AI is thinking…";

  try {
    const res = await fetch("/api/tutor/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    let data = {};
    try {
      data = await res.json();
    } catch {
      data = { ok: false, error: "Server returned non-JSON." };
    }

    // Handle backend error
    if (!res.ok || !data.ok) {
      const errMsg = data.error || `Server error (HTTP ${res.status})`;
      addMessage("ai", `Tutor failed to respond. ${errMsg}`.trim());
      status.textContent = "Error.";
      return;
    }

    // ✅ Correct key from Flask backend: data.answer
    const reply = (data.answer || "").trim();
    addMessage("ai", reply.length ? reply : "(No reply)");

    status.textContent = "Ready.";
  } catch (e) {
    addMessage("ai", "Tutor failed to respond. Network error.");
    status.textContent = "Network error.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");

  function submit() {
    const text = (input.value || "").trim();
    if (!text) return;

    addMessage("user", text);
    input.value = "";
    sendMessage(text);
  }

  sendBtn.addEventListener("click", submit);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") submit();
  });

  document.querySelectorAll(".prompt-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const p = btn.getAttribute("data-p");
      if (!p) return;
      input.value = p;
      input.focus();
    });
  });
});
