/**
 * API Service for NamanDarshan Ops AI
 */

export interface MessageItem {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: MessageItem[];
}

export interface ChatResponse {
  response: string;
  status: string;
}

export interface TableRow {
  [key: string]: any;
}

type AgentChatResponse = {
  reply: string;
  session_id: string;
  context: Record<string, unknown>;
  actions: Array<Record<string, unknown>>;
  rounds: number;
};

let sessionId: string | null = null;

const getApiBase = (): string => {
  // Prefer Vite env if provided: set `VITE_API_BASE=http://127.0.0.1:8000`
  const envBase = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
  if (envBase && envBase.trim()) return envBase.trim();

  // Check for production API URL
  const prodApiUrl = (import.meta as any)?.env?.VITE_API_URL as string | undefined;
  if (prodApiUrl && prodApiUrl.trim()) return prodApiUrl.trim();

  // If the frontend is not being served by the backend (8000) and no proxy is configured,
  // calls like `/api/...` will 404 on that frontend server. In that case, call backend directly.
  if (typeof window !== 'undefined' && window.location) {
    if (window.location.protocol === 'file:') return 'http://127.0.0.1:8000';
    const host = (window.location.hostname || '').toLowerCase();
    const port = window.location.port;
    if ((host === 'localhost' || host === '127.0.0.1') && port !== '8000') return 'http://127.0.0.1:8000';
    if (port && port !== '8000') return 'http://127.0.0.1:8000';
  }

  // Default: same-origin (backend-served frontend or Vite proxy)
  return '';
};

const apiUrl = (path: string): string => {
  const base = getApiBase();
  if (!base) return path;
  return new URL(path, base).toString();
};

export const sendMessage = async (messages: MessageItem[]): Promise<ChatResponse> => {
  const lastUser = [...messages].reverse().find(m => m.role === 'user');
  const message = lastUser?.content?.trim() ?? '';

  if (!message) {
    throw new Error('Message cannot be empty');
  }

  // 1. Try modern Agent API
  try {
    const url1 = apiUrl('/api/agent/chat');
    const res1 = await fetch(url1, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (res1.ok) {
      const data = (await res1.json()) as AgentChatResponse;
      sessionId = data.session_id;
      return { response: data.reply, status: 'ok' };
    }
    
    // If it's a 500 or other error (not 404), throw it so the user sees the real issue
    if (res1.status !== 404) {
       const errData = await res1.json().catch(() => ({ detail: 'Server Error' }));
       throw new Error(errData.detail || 'Agent API Error');
    }
  } catch (e: any) {
    if (e.message !== 'Failed to fetch' && !e.message.includes('404')) {
      throw e;
    }
  }

  // 2. Fallback to Legacy API (compatible with BOTH message formats now)
  const url2 = apiUrl('/api/chat');
  const res2 = await fetch(url2, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      messages: messages.map(m => ({ role: m.role, content: m.content }))
    }),
  });

  if (res2.ok) {
    const data = await res2.json();
    sessionId = data.session_id || sessionId;
    return { 
      response: data.response || data.reply || '', 
      status: data.status || 'ok' 
    };
  }

  const errData = await res2.json().catch(() => ({ detail: 'Failed to send message' }));
  throw new Error(errData.detail || 'Server encountered an error');
};

/**
 * Parses potential JSON table data from the AI's response string.
 * Expects the format: "Some text:\n[{\"key\": \"value\"}, ...]"
 */
export const parseTableData = (text: string): { cleanText: string; tableData: TableRow[] | null } => {
  if (text.includes(':\n[')) {
    const parts = text.split(':\n[');
    const cleanText = parts[0] + ':';
    try {
      const tableData = JSON.parse('[' + parts[1]);
      return { cleanText, tableData };
    } catch (e) {
      console.error("Failed to parse data", e);
    }
  }
  return { cleanText: text, tableData: null };
};
