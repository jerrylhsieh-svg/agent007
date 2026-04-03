const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendButtonEl = document.getElementById("send-button");
const statusEl = document.getElementById("status");

const history = [];

function addMessage(role, content) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;

  wrapper.appendChild(bubble);
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setLoading(isLoading) {
  inputEl.disabled = isLoading;
  sendButtonEl.disabled = isLoading;
  sendButtonEl.textContent = isLoading ? "Thinking..." : "Send";
}

async function checkHealth() {
  try {
    const res = await fetch("/health");
    const data = await res.json();
    statusEl.textContent = data.ok
      ? `Model ready: ${data.model}`
      : `Model unavailable: ${data.model}`;
  } catch {
    statusEl.textContent = "Backend unavailable";
  }
}

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();

  const message = inputEl.value.trim();
  if (!message) return;

  addMessage("user", message);
  history.push({ role: "user", content: message });
  inputEl.value = "";
  setLoading(true);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message,
        history: history.slice(-10)
      })
    });

    const data = await res.json();

    if (!res.ok) {
      addMessage("assistant", `Error: ${data.detail || "Unknown error"}`);
      return;
    }

    addMessage("assistant", data.reply);
    history.push({ role: "assistant", content: data.reply });
  } catch (err) {
    addMessage("assistant", `Error: ${err.message}`);
  } finally {
    setLoading(false);
    inputEl.focus();
  }
});

checkHealth();