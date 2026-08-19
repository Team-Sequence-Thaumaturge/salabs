// SA-CP Chrome Extension Side Panel Script (v5.0 True Live Stream Sync Engine)
// Polling GET http://127.0.0.1:8899/api/stream every 500ms so disk JSON updates immediately reflect on screen!

const chatContainer = document.getElementById('chatContainer');
const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');

let lastRenderedHash = "";

function renderMessages(messages) {
  const currentHash = JSON.stringify(messages);
  if (currentHash === lastRenderedHash) return;
  lastRenderedHash = currentHash;

  chatContainer.innerHTML = '';
  messages.forEach(msg => {
    const bubble = document.createElement('div');
    const isUser = msg.role === 'user';
    bubble.className = `chat-bubble ${isUser ? 'user' : 'assistant'}`;

    const senderDiv = document.createElement('div');
    senderDiv.className = 'sender-name';
    senderDiv.textContent = msg.sender || (isUser ? 'The Architect (시장님)' : 'Antigravity (SA-CP)');

    const textDiv = document.createElement('div');
    textDiv.textContent = msg.text;

    bubble.appendChild(senderDiv);
    bubble.appendChild(textDiv);
    chatContainer.appendChild(bubble);
  });
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function fetchLiveStream() {
  try {
    const resp = await fetch('http://127.0.0.1:8899/api/stream');
    if (resp.ok) {
      const data = await resp.json();
      const messages = data.chat_messages || [];
      renderMessages(messages);
    }
  } catch (e) {
    // Offline or server starting
  }
}

sendBtn.addEventListener('click', async () => {
  const text = msgInput.value.trim();
  if (!text) return;

  msgInput.value = '';

  try {
    const resp = await fetch('http://127.0.0.1:8899/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    if (resp.ok) {
      const data = await resp.json();
      renderMessages(data.chat_messages || []);
    }
  } catch (e) {
    console.error("Stream send failed:", e);
  }
});

msgInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendBtn.click();
  }
});

// Initial Stream Fetch & 500ms Polling Loop for 0-Latency Real-Time Screen Refresh
fetchLiveStream();
setInterval(fetchLiveStream, 500);
