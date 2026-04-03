front_page = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>agent007</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          max-width: 800px;
          margin: 40px auto;
          padding: 0 16px;
        }
        #chat {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 16px;
          min-height: 400px;
          margin-bottom: 16px;
          overflow-y: auto;
          background: #fafafa;
        }
        .msg {
          margin: 12px 0;
          padding: 10px 12px;
          border-radius: 8px;
          white-space: pre-wrap;
        }
        .user {
          background: #e8f0fe;
        }
        .bot {
          background: #f1f3f4;
        }
        .row {
          display: flex;
          gap: 8px;
        }
        input {
          flex: 1;
          padding: 12px;
          font-size: 16px;
        }
        button {
          padding: 12px 16px;
          font-size: 16px;
          cursor: pointer;
        }
      </style>
    </head>
    <body>
      <h1>agent007</h1>
      <div id="chat"></div>
      <div class="row">
        <input id="message" placeholder="Type a message..." />
        <button onclick="sendMessage()">Send</button>
      </div>

      <script>
        const chat = document.getElementById("chat");
        const input = document.getElementById("message");

        function addMessage(text, cls) {
          const div = document.createElement("div");
          div.className = `msg ${cls}`;
          div.textContent = text;
          chat.appendChild(div);
          chat.scrollTop = chat.scrollHeight;
        }

        async function sendMessage() {
          const message = input.value.trim();
          if (!message) return;

          addMessage("You: " + message, "user");
          input.value = "";

          try {
            const res = await fetch("/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message })
            });

            const data = await res.json();

            if (!res.ok) {
              addMessage("Error: " + (data.detail || JSON.stringify(data)), "bot");
              return;
            }

            addMessage("Agent: " + data.reply, "bot");
          } catch (err) {
            addMessage("Error: " + err.message, "bot");
          }
        }

        input.addEventListener("keydown", (e) => {
          if (e.key === "Enter") sendMessage();
        });
      </script>
    </body>
    </html>
    """