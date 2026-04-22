/**
 * app.js — NamanDarshan frontend application logic
 * Handles chat, data panels, session, and UI state.
 */

import * as API from './api.js';

// ── State ─────────────────────────────────────────────────────────────────
let sessionId   = null;
let liveData    = {};
let isThinking  = false;
let currentTab  = 'pandits';

// ── DOM refs ──────────────────────────────────────────────────────────────
const msgList     = document.getElementById('messages');
const msgInput    = document.getElementById('msg-input');
const sendBtn     = document.getElementById('send-btn');
const statusPill  = document.getElementById('status-pill');
const statusDot   = statusPill.querySelector('.dot');
const appRoot     = document.getElementById('app');
const mobileOverlay = document.getElementById('mobile-overlay');

function syncMobileOverlay() {
  if (!appRoot || !mobileOverlay) return;
  const open = appRoot.classList.contains('show-sidebar') || appRoot.classList.contains('show-data-panel');
  mobileOverlay.classList.toggle('open', open);
}

window.toggleSidebar = function() {
  if (!appRoot) return;
  appRoot.classList.toggle('show-sidebar');
  appRoot.classList.remove('show-data-panel');
  syncMobileOverlay();
};

window.toggleDataPanel = function() {
  if (!appRoot) return;
  appRoot.classList.toggle('show-data-panel');
  appRoot.classList.remove('show-sidebar');
  syncMobileOverlay();
};

window.closePanels = function() {
  if (!appRoot) return;
  appRoot.classList.remove('show-sidebar', 'show-data-panel');
  syncMobileOverlay();
};

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') window.closePanels?.();
});

// ── Boot ──────────────────────────────────────────────────────────────────
async function boot() {
  setStatus('connecting');
  try {
    const health = await API.getHealth();
    setStatus('online');
    const sheets = Array.isArray(health?.sheets) ? health.sheets : null;
    await loadAllData(sheets);
  } catch {
    setStatus('offline');
  }
}

function setStatus(state) {
  const map = {
    connecting: ['Connecting…', '#A89880'],
    online:     ['Online',      '#1D9E75'],
    offline:    ['Offline',     '#c0392b'],
  };
  const [label, color] = map[state] || map.connecting;
  statusPill.childNodes[statusPill.childNodes.length - 1].textContent = ' ' + label;
  statusDot.style.background = color;
}

// ── Data loading ──────────────────────────────────────────────────────────
async function loadAllData(sheetsFromServer) {
  const fallbackSheets = ['Pandits', 'Hotels', 'Cabs'];
  const sheets = (Array.isArray(sheetsFromServer) && sheetsFromServer.length)
    ? sheetsFromServer
    : fallbackSheets;

  await Promise.allSettled(
    sheets.map(s =>
      API.getSheetData(s)
        .then(r => { liveData[s] = r.data; })
        .catch(() => {})
    ));  updateStatsPanel();
  renderDataTab(currentTab);
  renderTemples();
}

function updateStatsPanel() {
  const avP = (liveData.Pandits || []).filter(r => r.Available === 'Yes').length;
  const avC = (liveData.Cabs    || []).filter(r => r.Available === 'Yes').length;
  setText('stat-pandits', avP);
  setText('stat-cabs',    avC);
  setText('stat-hotels',  (liveData.Hotels  || []).length);
  setText('stat-temples', (liveData.Temples || []).length);
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ── Data tab renderer ─────────────────────────────────────────────────────
function renderDataTab(tab) {
  currentTab = tab;
  const body  = document.getElementById('panel-body');
  const map   = { pandits: 'Pandits', hotels: 'Hotels', cabs: 'Cabs' };
  const data  = liveData[map[tab]] || [];

  if (!data.length) {
    body.innerHTML = '<div class="empty-state">No data loaded</div>';
    return;
  }

  body.innerHTML = data.map(r => {
    if (tab === 'pandits') return `
      <div class="data-card">
        <div class="dc-name">${r.Name}</div>
        <div class="dc-meta">${r.Specialization}</div>
        <div class="dc-meta">${r.Location} · ₹${r.Price_Per_Puja}
          · <span class="${r.Available === 'Yes' ? 'avail-yes' : 'avail-no'}">${r.Available === 'Yes' ? '✓ Available' : '✗ Busy'}</span>
        </div>
      </div>`;
    if (tab === 'hotels') return `
      <div class="data-card">
        <div class="dc-name">${r.Name}</div>
        <div class="dc-meta">${r.City} · ${'★'.repeat(r.Star_Rating || 1)} · ₹${r.Price_Per_Night}/night</div>
        <div class="dc-meta">${r.Rooms_Available} rooms · ${r.Distance_From_Temple_km} km to temple</div>
      </div>`;
    if (tab === 'cabs') return `
      <div class="data-card">
        <div class="dc-name">${r.Driver_Name} — ${r.Vehicle_Type}</div>
        <div class="dc-meta">${r.City} · ₹${r.Price_Per_Km}/km · ${r.Capacity} seats</div>
        <div class="dc-meta">⭐ ${r.Rating}
          · <span class="${r.Available === 'Yes' ? 'avail-yes' : 'avail-no'}">${r.Available === 'Yes' ? '✓ Available' : '✗ Busy'}</span>
        </div>
      </div>`;
    return '';
  }).join('');
}

function renderTemples() {
  const body = document.getElementById('temples-body');
  if (!body) return;
  const data = liveData.Temples || [];
  body.innerHTML = data.length
    ? data.map(r => `
        <div class="data-card">
          <div class="dc-name">${r.Name}</div>
          <div class="dc-meta">${r.City} · ${r.Deity}</div>
          <div class="dc-meta">${r.Opening_Time} – ${r.Closing_Time}</div>
        </div>`).join('')
    : '<div class="empty-state">No temple data</div>';
}

// Tab switching
window.switchTab = function(tab, btn) {
  document.querySelectorAll('.p-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  renderDataTab(tab);
};

// ── Chat ──────────────────────────────────────────────────────────────────
function appendMsg(role, html, actions) {
  const wrap   = document.createElement('div');
  wrap.className = `msg ${role}`;

  const av   = document.createElement('div');
  av.className = `msg-avatar ${role}`;
  av.textContent = role === 'bot' ? 'ND' : 'You';

  const bub  = document.createElement('div');
  bub.className = 'msg-bubble';
  bub.innerHTML = html.replace(/\n/g, '<br>');

  // Show tool badges if actions present
  if (actions && actions.length) {
    const trace = document.createElement('div');
    trace.className = 'tool-trace';
    actions.forEach(a => {
      const badge = document.createElement('span');
      badge.className = 'tool-badge';
      badge.textContent = '🔧 ' + a.tool;
      trace.appendChild(badge);
    });
    bub.appendChild(trace);
  }

  wrap.appendChild(av);
  wrap.appendChild(bub);
  msgList.appendChild(wrap);
  msgList.scrollTop = msgList.scrollHeight;
}

function showTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'msg bot'; wrap.id = 'typing-wrap';
  const av = document.createElement('div');
  av.className = 'msg-avatar bot'; av.textContent = 'ND';
  const bub = document.createElement('div');
  bub.className = 'msg-bubble typing-dots';
  bub.innerHTML = '<span></span><span></span><span></span>';
  wrap.appendChild(av); wrap.appendChild(bub);
  msgList.appendChild(wrap);
  msgList.scrollTop = msgList.scrollHeight;
}

function removeTyping() {
  document.getElementById('typing-wrap')?.remove();
}

async function doSend(text) {
  if (isThinking || !text.trim()) return;
  isThinking = true;
  sendBtn.disabled = true;

  appendMsg('user', text);
  showTyping();

  try {
    const res = await API.sendMessage(text, sessionId);
    sessionId = res.session_id;
    removeTyping();
    appendMsg('bot', res.reply, res.actions);
    updateContextPanel(res.context);
  } catch (err) {
    removeTyping();
    const raw = (err && err.message) ? String(err.message) : 'Unknown error';
    const hint =
      raw.includes('Chat endpoints failed') || raw.includes('/api/agent/chat=404') || raw.includes('404')
        ? 'Backend not connected. Start it with: <code>cd Backend; python main.py</code> then refresh.'
        : 'Please try again.';
    appendMsg('bot', `Sorry Ji, I couldn't reach the server 🙏<br><small>${hint}</small>`);
  } finally {
    isThinking = false;
    sendBtn.disabled = false;
    msgInput.focus();
  }
}

function updateContextPanel(context) {
  const body = document.getElementById('context-body');
  if (!body) return;
  const entries = Object.entries(context || {});
  if (!entries.length) {
    body.innerHTML = '<div class="empty-state">No preferences remembered yet</div>';
    return;
  }
  body.innerHTML = entries.map(([k, v]) => `
    <div class="context-row">
      <span class="context-key">${k.replace(/_/g,' ')}</span>
      <span class="context-val">${v}</span>
    </div>`).join('');
}

// ── Event handlers ────────────────────────────────────────────────────────
msgInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
});

window.handleSend = function() {
  const val = msgInput.value.trim();
  if (!val) return;
  msgInput.value = '';
  doSend(val);
};

window.sendChip = function(btn) {
  const text = btn.textContent.replace(/^[^\w]+/, '').trim();
  btn.disabled = true;
  doSend(text);
};

window.sendQuick = function(text) { doSend(text); };

// ── Excel upload / reload ─────────────────────────────────────────────────
window.openUpload = function() {
  document.getElementById('upload-overlay').classList.add('open');
};
window.closeUpload = function() {
  document.getElementById('upload-overlay').classList.remove('open');
};

window.doUpload = async function() {
  const file = document.getElementById('excel-file-input').files[0];
  if (!file) return alert('Please select an Excel file first.');
  try {
    await API.uploadExcel(file);
    closeUpload();
    await loadAllData();
    appendMsg('bot', '✅ Excel data updated and reloaded successfully Ji!');
  } catch (err) {
    alert('Upload failed: ' + err.message);
  }
};

window.doReload = async function() {
  try {
    await API.reloadExcel();
    await loadAllData();
    appendMsg('bot', '🔄 Data refreshed from Excel 🙏');
  } catch (err) {
    alert('Reload failed: ' + err.message);
  }
};

window.clearChat = function() {
  msgList.innerHTML = '';
  if (sessionId) API.clearSession(sessionId).catch(() => {});
  sessionId = null;
  updateContextPanel({});
  appendMsg('bot', '🙏 Namaste Ji! New conversation started. How can I help you today?');
};

// ── Start ─────────────────────────────────────────────────────────────────
boot();
