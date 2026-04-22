/**
 * api.js — frontend API client for NamanDarshan backend
 *
 * This file is imported by `Frontend/assets/app.js`.
 * All calls use relative `/api/...` paths so it works when:
 * - served by the backend (same origin), or
 * - served by Vite with `/api` proxy (see `Frontend/vite.config.ts`).
 */

async function readError(res) {
  try {
    const data = await res.json();
    if (data && typeof data === 'object' && data.detail) return String(data.detail);
    return JSON.stringify(data);
  } catch {
    try {
      return await res.text();
    } catch {
      return `${res.status} ${res.statusText}`;
    }
  }
}

function getApiBase() {
  // Optional override: set `window.__ND_API_BASE__ = "http://127.0.0.1:8000"` in dev.
  if (typeof window !== 'undefined' && window.__ND_API_BASE__) return String(window.__ND_API_BASE__);

  // If the frontend is not being served by the backend (8000) and no proxy is configured,
  // calls like `/api/...` will 404 on that frontend server. In that case, call backend directly.
  if (typeof window !== 'undefined' && window.location) {
    if (window.location.protocol === 'file:') return 'http://127.0.0.1:8000';
    const port = window.location.port; // '' for default (80/443)
    const host = (window.location.hostname || '').toLowerCase();
    if ((host === 'localhost' || host === '127.0.0.1') && port !== '8000') return 'http://127.0.0.1:8000';
    if (port && port !== '8000') return 'http://127.0.0.1:8000';
  }

  // Default: same-origin (works when backend serves the frontend or when Vite proxy is enabled).
  return '';
}

function apiUrl(path) {
  const base = getApiBase();
  if (!base) return path;
  return new URL(path, base).toString();
}

async function requestJson(path, options) {
  const url = apiUrl(path);
  const res = await fetch(url, options);
  if (!res.ok) {
    const detail = await readError(res);
    throw new Error(detail || `Request failed: ${res.status} ${res.statusText} (${url})`);
  }
  return res.json();
}

export function getHealth() {
  return requestJson('/api/health', { method: 'GET' });
}

export function getSheetData(sheet) {
  return requestJson(`/api/data/${encodeURIComponent(sheet)}`, { method: 'GET' });
}

export function sendMessage(message, sessionId) {
  return (async () => {
    // 1. Try modern Agent API
    try {
      const url1 = apiUrl('/api/agent/chat');
      const res1 = await fetch(url1, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId || null }),
      });

      if (res1.ok) {
        const data = await res1.json();
        return {
          reply: data.reply || '',
          session_id: data.session_id || sessionId || null,
          context: data.context || {},
          actions: data.actions || [],
          rounds: data.rounds || 1,
        };
      }
      
      if (res1.status !== 404) {
        const detail = await readError(res1);
        throw new Error(detail || `Agent API Error: ${res1.status}`);
      }
    } catch (e) {
      if (!e.message.includes('404') && e.message !== 'Failed to fetch') throw e;
    }

    // 2. Fallback to Legacy API (using messages array for compatibility)
    const url2 = apiUrl('/api/chat');
    const res2 = await fetch(url2, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId || null,
        message: message, // Support both formats
        messages: [{ role: 'user', content: message }],
      }),
    });

    if (res2.ok) {
      const data = await res2.json();
      return {
        reply: data.response || data.reply || '',
        session_id: data.session_id || sessionId || null,
        context: data.context || {},
        actions: data.actions || [],
        rounds: data.rounds || 1,
      };
    }

    const detail = await readError(res2);
    throw new Error(detail || `Chat failed: ${res2.status}`);
  })();
}

  /*
  return requestJson('/api/agent/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId || null,
    }),
  });
  */

export function reloadExcel() {
  return requestJson('/api/excel/reload', { method: 'POST' });
}

export function uploadExcel(file) {
  const form = new FormData();
  form.append('file', file);
  return requestJson('/api/excel/upload', {
    method: 'POST',
    body: form,
  });
}

export function clearSession(sessionId) {
  if (!sessionId) return Promise.resolve({ deleted: false, session_id: null });
  return requestJson(`/api/agent/session/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
}
