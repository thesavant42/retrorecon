// RetroRecon chat overlay for natural language questions.
// Users should type plain English queries. The server uses an
// LLM to translate requests into safe SQL before execution.
window.retroChat = (function() {
  const overlay = document.querySelector('.chat-overlay');
  const messages = overlay.querySelector('.chat-overlay__messages');
  const input = overlay.querySelector('.chat-overlay__input-field');
  const sendBtn = overlay.querySelector('.chat-overlay__send');
  const closeBtn = overlay.querySelector('.chat-overlay__close');
  const resizeHandle = overlay.querySelector('.chat-overlay__resize');

  let resizing = false;
  let startX = 0;
  let startWidth = 0;

  function show() {
    overlay.classList.add('show');
    overlay.classList.remove('hidden');
    input.focus();
  }

  function hide() {
    overlay.classList.add('hidden');
    overlay.classList.remove('show');
  }

  function startResize(e) {
    resizing = true;
    startX = e.clientX;
    startWidth = overlay.offsetWidth;
    document.addEventListener('mousemove', onResize);
    document.addEventListener('mouseup', stopResize);
    e.preventDefault();
  }

  function onResize(e) {
    if (!resizing) return;
    const dx = startX - e.clientX;
    let newWidth = startWidth + dx;
    const min = 300;
    const max = window.innerWidth * 0.9;
    newWidth = Math.max(min, Math.min(max, newWidth));
    overlay.style.width = newWidth + 'px';
  }

  function stopResize() {
    resizing = false;
    document.removeEventListener('mousemove', onResize);
    document.removeEventListener('mouseup', stopResize);
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
    if (data.message) {
      appendMessage('LLM: ' + data.message);
    } else if (data.error) {
      const hint = data.hint ? '\n' + data.hint : '';
      appendMessage('Error: ' + data.error + hint);
    } else {
      appendMessage(JSON.stringify(data, null, 2));
    }
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
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('show')) {
      hide();
    } else if (e.key === '~' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      if (overlay.classList.contains('show')) {
        hide();
      } else {
        show();
      }
    }
  });

  if (resizeHandle) resizeHandle.addEventListener('mousedown', startResize)
  document.addEventListener('DOMContentLoaded', () => {
    const link = document.getElementById('chat-link');
    if (link) {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        if (typeof closeMenus === 'function') closeMenus();
        show();
      });
    }
  });

  return { show, hide };
})();
