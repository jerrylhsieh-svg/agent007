const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendButtonEl = document.getElementById("send-button");
const statusEl = document.getElementById("status");
const sessionId = crypto.randomUUID();
const fileInput = document.getElementById("file-file");
const uploadBtn = document.getElementById("upload-btn");
const fileForm = document.getElementById("file-form");

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
  fileInput.disabled = isLoading;
  uploadBtn.disabled = isLoading;
  uploadBtn.textContent = isLoading ? "Uploading..." : "Upload file";
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

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileNameEl.textContent = file ? file.name : "";
});

uploadBtn.addEventListener("click", async (e) => {
  e.preventDefault();

  const file = fileInput?.files?.[0];
  if (!file) {
    addMessage("assistant", "Please choose a file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const ext = getFileExtension(file.name);
  let url;
  if (ext === "pdf") {
    url = "/pdf/extract";
  } else {
    url = "/training/upload-labeled-csv";
    
  }

  try {
    setLoading(true);
    setUploading(true);
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      addMessage("assistant", `File upload failed: ${data.detail || "Unknown error"}`);
      return;
    }

    addMessage(
      "assistant",
      `Uploaded ${data.filename || file.name} successfully.`
    );
    fileForm.reset();
  } catch (err) {
    addMessage("assistant", `File upload failed: ${err.message}`);
  } finally {
    setLoading(false);
    setUploading(false);

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