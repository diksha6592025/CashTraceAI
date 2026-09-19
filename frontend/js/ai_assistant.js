/* CashTrace AI — floating RAG assistant
   UI-only client. Backend endpoint remains /api/ai-assistant/chat.
*/
(() => {
  const API_URL = '/api/ai-assistant/chat';

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[ch]));
  }

  function ensureWidget() {
    if (document.querySelector('.ai-assistant-widget')) return;
    const root = document.createElement('div');
    root.className = 'ai-assistant-widget';
    root.innerHTML = `
      <button class="ai-assistant-btn" id="cashtrace-rag-toggle"
              type="button" aria-label="Open CashTrace AI Assistant"
              aria-expanded="false" title="CashTrace AI Assistant">🤖</button>
      <section class="ai-chat-window" id="ai-chat-window"
               role="dialog" aria-label="CashTrace AI Assistant" aria-hidden="true">
        <header class="ai-chat-header">
          <div class="ai-chat-title">
            <span class="ai-chat-icon">🤖</span>
            <div>
              <strong>CashTrace AI Assistant</strong>
              <small>RAG + Gemini AI</small>
            </div>
          </div>
          <button class="ai-chat-close" id="cashtrace-rag-close" type="button"
                  aria-label="Close assistant">✕</button>
        </header>
        <div class="ai-chat-body" id="ai-chat-body" aria-live="polite">
          <div class="ai-msg ai-msg-bot">
            👋 <strong>Namaste!</strong> I am your CashTrace AI Assistant.
            Ask me about fund lineage, cash-out forecasting, cyber safety, or how CashTrace AI works!
          </div>
          <div class="ai-quick-chips" id="ai-quick-chips">
            <button class="ai-chip" type="button" data-prompt="How does CashTrace AI predict ATM cash withdrawal hotspots?">🧠 ATM Cash Prediction</button>
            <button class="ai-chip" type="button" data-prompt="I got scammed on UPI. What should I do?">💳 UPI Scam Advice</button>
            <button class="ai-chip" type="button" data-prompt="How to file a cyber complaint on CashTrace AI?">📄 How to File Complaint</button>
            <button class="ai-chip" type="button" data-prompt="What is the Golden Hour and 1930 Helpline?">☎ 1930 Golden Hour</button>
          </div>
        </div>
        <footer class="ai-chat-footer">
          <input type="text" class="ai-chat-input" id="ai-chat-input"
                 placeholder="Ask about safety, fund lineage, or CashTrace AI..."
                 autocomplete="off" aria-label="Ask CashTrace AI">
          <button class="ai-chat-send" id="ai-send-btn" type="button">Send</button>
        </footer>
      </section>
    `;
    document.body.appendChild(root);

    const toggle = root.querySelector('#cashtrace-rag-toggle');
    const close = root.querySelector('#cashtrace-rag-close');
    const input = root.querySelector('#ai-chat-input');
    const send = root.querySelector('#ai-send-btn');

    toggle.addEventListener('click', e => {
      e.stopPropagation();
      if (root.querySelector('#ai-chat-window').classList.contains('is-open')) closeChatWindow();
      else openChatWindow();
    });
    close.addEventListener('click', e => { e.stopPropagation(); closeChatWindow(); });
    send.addEventListener('click', sendChatMessage);
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); sendChatMessage(); }
    });
    root.querySelectorAll('.ai-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        input.value = chip.dataset.prompt || '';
        sendChatMessage();
      });
    });

    document.addEventListener('pointerdown', e => {
      const win = root.querySelector('#ai-chat-window');
      if (win.classList.contains('is-open') && !root.contains(e.target)) closeChatWindow();
    }, true);

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeChatWindow();
    });

    document.addEventListener('click', e => {
      const link = e.target.closest('a[href]');
      if (link && !root.contains(link)) closeChatWindow();
    }, true);
  }

  function openChatWindow() {
    const win = document.getElementById('ai-chat-window');
    const btn = document.getElementById('cashtrace-rag-toggle');
    if (!win) return;
    win.classList.add('is-open');
    win.setAttribute('aria-hidden', 'false');
    if (btn) btn.setAttribute('aria-expanded', 'true');
    const input = document.getElementById('ai-chat-input');
    if (input) setTimeout(() => input.focus(), 0);
  }

  function closeChatWindow() {
    const win = document.getElementById('ai-chat-window');
    const btn = document.getElementById('cashtrace-rag-toggle');
    if (!win) return;
    win.classList.remove('is-open');
    win.setAttribute('aria-hidden', 'true');
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }

  async function sendChatMessage() {
    const input = document.getElementById('ai-chat-input');
    const body = document.getElementById('ai-chat-body');
    const send = document.getElementById('ai-send-btn');
    if (!input || !body || !send) return;
    const text = input.value.trim();
    if (!text || send.disabled) return;

    body.insertAdjacentHTML('beforeend',
      `<div class="ai-msg ai-msg-user">${esc(text)}</div>`);
    input.value = '';
    input.disabled = true;
    send.disabled = true;

    const typing = document.createElement('div');
    typing.className = 'ai-typing';
    typing.textContent = '🤖 CashTrace AI is thinking…';
    body.appendChild(typing);
    body.scrollTop = body.scrollHeight;

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30000);
      const response = await fetch(API_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {'Content-Type':'application/json','Accept':'application/json'},
        body: JSON.stringify({message: text}),
        signal: controller.signal,
        cache: 'no-store'
      });
      clearTimeout(timeout);

      let data = {};
      try { data = await response.json(); } catch (_) {}
      typing.remove();

      if (!response.ok) {
        throw new Error(data.message || `Server returned HTTP ${response.status}`);
      }

      let answer = String(data.response || 'No response received.');
      const msg = document.createElement('div');
      msg.className = 'ai-msg ai-msg-bot';
      msg.innerHTML = esc(answer)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
      if (data.powered_by) {
        const source = document.createElement('small');
        source.className = 'ai-powered-by';
        source.textContent = '⚡ ' + data.powered_by;
        msg.appendChild(source);
      }
      body.appendChild(msg);
    } catch (err) {
      typing.remove();
      const msg = document.createElement('div');
      msg.className = 'ai-msg ai-msg-bot ai-error';
      msg.textContent = err.name === 'AbortError'
        ? '⚠️ The AI service took too long to respond. Please try again.'
        : '⚠️ Connection error. Please try again.';
      body.appendChild(msg);
    } finally {
      input.disabled = false;
      send.disabled = false;
      input.focus();
      body.scrollTop = body.scrollHeight;
    }
  }

  window.toggleChatWindow = function() {
    const win = document.getElementById('ai-chat-window');
    if (win?.classList.contains('is-open')) closeChatWindow();
    else openChatWindow();
  };
  window.closeChatWindow = closeChatWindow;
  window.askQuickPrompt = function(prompt) {
    const input = document.getElementById('ai-chat-input');
    if (input) { input.value = prompt; sendChatMessage(); }
  };
  window.sendChatMessage = sendChatMessage;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureWidget, {once:true});
  } else {
    ensureWidget();
  }
})();
