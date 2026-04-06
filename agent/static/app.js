const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendButtonEl = document.getElementById("send-button");
const statusEl = document.getElementById("status");
const sessionId = crypto.randomUUID();

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

async function uploadPdf(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/pdf/extract", {
    method: "POST",
    body: formData
  });

  return await response.json();
}

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();

  const file = document.getElementById("pdf-file").files[0];
  if (file) {
    const pdfResult = await uploadPdf(file);
    console.log("PDF extracted:", pdfResult);
  }

  const message = inputEl.value.trim();
  const response = await sendMessage(message, history);
  addMessage("assistant", response.reply);

  
  if (!message) return;

  addMessage("user", message);
  history.push({ role: "user", content: message });
  inputEl.value = "";
  setLoading(true);

  try {
    const res =  await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message: message,
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