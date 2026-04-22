import { useState, useEffect, useRef } from 'react';
import { Bot, Send, ShieldCheck, Globe, Database } from 'lucide-react';
import { sendMessage, parseTableData, TableRow } from './services/api';
import DataTable from './components/DataTable';

interface Message {
  text: string;
  role: 'user' | 'ai';
  timestamp: string;
  data?: TableRow[] | null;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      text: "Namaste! I am your NamanDarshan Ops AI Agent. I'm connected to your internal records and namandarshan.com. How can I assist with your temple operations today?",
      role: 'ai',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      text: input.trim(),
      role: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const history = newMessages.map(m => ({
        role: (m.role === 'ai' ? 'assistant' : 'user') as 'assistant' | 'user',
        content: m.text
      }));

      const data = await sendMessage(history);
      const { cleanText, tableData } = parseTableData(data.response);

      const aiMessage: Message = {
        text: cleanText,
        role: 'ai',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        data: tableData
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages(prev => [...prev, {
        text: "I encountered an issue connecting to my services. Please verify the backend status.",
        role: 'ai',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <div className="logo-section">
          <div className="logo-icon">
            <Bot size={28} color="white" strokeWidth={2.5} />
          </div>
          <div className="logo-text">
            <h1>NamanDarshan Ops Agent</h1>
            <p className="flex items-center gap-2">
              <Database size={12} className="inline mr-1" /> Excel Data + <Globe size={12} className="inline mr-1" /> Live Web Verification
            </p>
          </div>
        </div>
        <div className="status-badge">
          <ShieldCheck size={16} className="text-green-600" />
          Real-time Agent Active
          <div className="status-dot"></div>
        </div>
      </header>

      <div id="chat-area" ref={chatAreaRef}>
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.text}
              {msg.data && <DataTable data={msg.data} />}
            </div>
            <div className="timestamp">{msg.timestamp}</div>
          </div>
        ))}
        {isLoading && (
          <div className="message ai">
            <div className="message-content typing">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
        )}
      </div>

      <div className="input-container">
        <form id="chat-form" onSubmit={handleSend}>
          <div className="input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your request (e.g., 'Find available Pandits in Varanasi')"
              autoComplete="off"
              disabled={isLoading}
            />
            <button type="submit" className="send-btn" disabled={isLoading || !input.trim()}>
              <Send size={20} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;
