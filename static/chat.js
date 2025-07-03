// RetroRecon chat overlay for natural language questions.
// Users should type plain English queries. The server uses an
// LLM to translate requests into safe SQL before execution.
window.retroChat = (function() {
  const overlay = document.querySelector('.chat-overlay');
  const messages = overlay.querySelector('.chat-overlay__messages');
  const input = overlay.querySelector('.chat-overlay__input-field');
  const sendBtn = overlay.querySelector('.chat-overlay__send');
  const closeBtn = overlay.querySelector('.chat-overlay__close');

  function show() {
    overlay.classList.remove('hidden');
    input.focus();
  }

  function hide() {
    overlay.classList.add('hidden');
  }

  // Send the user's natural language query to the backend
  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    appendMessage('> ' + text);
    const resp = await fetch('/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await resp.json();
    appendMessage(JSON.stringify(data, null, 2));
  }

  function appendMessage(text) {
    const pre = document.createElement('pre');
    pre.textContent = text;
    messages.appendChild(pre);
    messages.scrollTop = messages.scrollHeight;
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
  if (closeBtn) closeBtn.addEventListener('click', hide);

  document.addEventListener('DOMContentLoaded', () => {
    const link = document.getElementById('chat-link');
    if (link) {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        show();
      });
    }
  });

  return { show, hide };
})();
