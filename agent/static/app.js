const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendButtonEl = document.getElementById("send-button");
const statusEl = document.getElementById("status");
const sessionId = crypto.randomUUID();
const pdfInput = document.getElementById("pdf-file");
const uploadPdfBtn = document.getElementById("upload-btn");
const pdfForm = document.getElementById("pdf-form");

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

function setUploading(isLoading) {
  pdfInput.disabled = isLoading;
  uploadPdfBtn.disabled = isLoading;
  uploadPdfBtn.textContent = isLoading ? "Uploading..." : "Upload PDF";
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

pdfInput.addEventListener("change", () => {
  const file = pdfInput.files[0];
  fileNameEl.textContent = file ? file.name : "";
});

uploadPdfBtn.addEventListener("click", async (e) => {
  e.preventDefault();

  const file = pdfInput?.files?.[0];
  if (!file) {
    addMessage("assistant", "Please choose a PDF first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    setLoading(true);
    setUploading(true);
    const response = await fetch("/pdf/extract", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      addMessage("assistant", `PDF upload failed: ${data.detail || "Unknown error"}`);
      return;
    }

    addMessage(
      "assistant",
      `Uploaded ${data.filename || file.name} successfully.`
    );
    pdfForm.reset();
  } catch (err) {
    addMessage("assistant", `PDF upload failed: ${err.message}`);
  } finally {
    setLoading(false);

  }
  
});


formEl.addEventListener("submit", async (e) => {
  e.preventDefault();

  const message = inputEl.value.trim();
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