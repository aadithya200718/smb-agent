import './DemoRunner.css';
import { useState, useRef, useEffect } from 'react';
import {
  Send, Bot, User, Smartphone, Terminal, Zap, CheckCircle, XCircle,
  AlertTriangle, Clock, ChefHat, RefreshCw, Loader2, Coffee,
  Menu as MenuIcon, ShoppingCart
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

/* ─── trace‑log color mapping ───────────────────────────────────── */
const NODE_STYLES = {
  input:   { color: '#60a5fa', icon: Zap,           label: 'INPUT' },
  think:   { color: '#c084fc', icon: Bot,            label: 'THINK' },
  plan:    { color: '#facc15', icon: MenuIcon,       label: 'PLAN' },
  act:     { color: '#34d399', icon: ShoppingCart,    label: 'ACT' },
  review:  { color: '#f472b6', icon: CheckCircle,    label: 'REVIEW' },
  update:  { color: '#fb923c', icon: RefreshCw,      label: 'UPDATE' },
  respond: { color: '#38bdf8', icon: Send,           label: 'RESPOND' },
};

/* ─── single trace entry component ──────────────────────────────── */
function TraceEntry({ entry, index, visible }) {
  const style = NODE_STYLES[entry.node_name] || NODE_STYLES.input;
  const Icon = style.icon;

  return (
    <div
      className={`trace-entry ${visible ? 'trace-visible' : ''}`}
      style={{
        animationDelay: `${index * 400}ms`,
        borderLeft: `3px solid ${style.color}`,
      }}
    >
      <div className="trace-header">
        <span className="trace-badge" style={{ background: style.color + '22', color: style.color }}>
          <Icon size={13} />
          {style.label}
        </span>
        <span className="trace-time">{new Date(entry.timestamp).toLocaleTimeString()}</span>
      </div>

      {entry.decision && (
        <div className="trace-decision">→ {entry.decision}</div>
      )}

      {entry.output_summary && Object.keys(entry.output_summary).length > 0 && (
        <pre className="trace-json">
          {JSON.stringify(entry.output_summary, null, 2)}
        </pre>
      )}
    </div>
  );
}


/* ─── chat bubble ───────────────────────────────────────────────── */
function ChatBubble({ role, text, time }) {
  const isUser = role === 'user';
  return (
    <div className={`chat-bubble-wrap ${isUser ? 'chat-user' : 'chat-bot'}`}>
      <div className={`chat-bubble ${isUser ? 'bubble-user' : 'bubble-bot'}`}>
        <p>{text}</p>
        <span className="bubble-time">{time}</span>
      </div>
    </div>
  );
}


/* ─── Quick Suggestion Chips ─────────────────────────────────── */
const SUGGESTIONS = [
  "Show me the menu",
  "I want 2 Chicken Biryani",
  "Order 1 Paneer Butter Masala",
  "What desserts do you have?",
  "3 Butter Naan please",
  "I want Masala Dosa and Mango Lassi",
];


/* ═══════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════════════════ */
export default function DemoRunner() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Welcome to Spice Route QSR! 🍛\nI can help you browse our menu, place orders, and handle payments.\n\nWhat would you like today?', time: now() },
  ]);
  const [traceEntries, setTraceEntries] = useState([]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [menuItems, setMenuItems] = useState([]);
  const [showMenu, setShowMenu] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [stats, setStats] = useState({ total: 0, avgTime: 0, retries: 0 });

  const chatEndRef = useRef(null);
  const traceEndRef = useRef(null);
  const inputRef = useRef(null);

  /* auto-scroll */
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  useEffect(() => { traceEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [visibleCount]);

  /* staggered trace reveal */
  useEffect(() => {
    if (visibleCount < traceEntries.length) {
      const timer = setTimeout(() => setVisibleCount(c => c + 1), 450);
      return () => clearTimeout(timer);
    }
  }, [visibleCount, traceEntries.length]);

  /* fetch menu list */
  async function loadMenu() {
    try {
      const res = await fetch(`${API_BASE}/demo/menu`);
      const data = await res.json();
      setMenuItems(data.items || []);
      setShowMenu(true);
    } catch { setMenuItems([]); }
  }

  /* seed 25 items */
  async function seedMenu() {
    setSeeding(true);
    try {
      await fetch(`${API_BASE}/demo/seed-menu`, { method: 'POST' });
      await loadMenu();
    } catch (e) { console.error(e); }
    setSeeding(false);
  }

  /* send message */
  async function handleSend(overrideText) {
    const text = (overrideText || input).trim();
    if (!text || loading) return;

    const userTime = now();
    setMessages(prev => [...prev, { role: 'user', text, time: userTime }]);
    setInput('');
    setLoading(true);

    const t0 = performance.now();

    try {
      const res = await fetch(`${API_BASE}/demo/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, phone_number: '+919876543210' }),
      });
      const data = await res.json();
      const elapsed = ((performance.now() - t0) / 1000).toFixed(1);

      setMessages(prev => [...prev, {
        role: 'bot',
        text: data.reply || 'No response',
        time: now(),
      }]);

      // Append new trace log entries
      setTraceEntries(prev => {
        const newEntries = [...prev, ...data.trace_log];
        setVisibleCount(prev.length); // start animating from where we left off
        return newEntries;
      });

      setStats(s => ({
        total: s.total + 1,
        avgTime: ((s.avgTime * s.total + parseFloat(elapsed)) / (s.total + 1)).toFixed(1),
        retries: s.retries + (data.retry_count || 0),
      }));
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: '⚠️ Could not reach the backend. Please check the API server and Vite proxy/API URL.',
        time: now(),
      }]);
    }
    setLoading(false);
    inputRef.current?.focus();
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  /* ─── Render ──────────────────────────────────────────────────── */
  return (
    <div className="demo-root">
      {/* ── TOP BAR ─────────────────────────────────────────────── */}
      <header className="demo-topbar">
        <div className="topbar-left">
          <ChefHat size={22} className="topbar-icon" />
          <h1>Spice Route QSR <span className="topbar-tag">AI Agent Demo</span></h1>
        </div>
        <div className="topbar-right">
          <div className="stat-pill"><Coffee size={14} /> <span>{stats.total} msgs</span></div>
          <div className="stat-pill"><Clock size={14} /> <span>{stats.avgTime}s avg</span></div>
          <div className="stat-pill"><RefreshCw size={14} /> <span>{stats.retries} retries</span></div>
          <button className="seed-btn" onClick={seedMenu} disabled={seeding}>
            {seeding ? <Loader2 size={14} className="spin" /> : <Zap size={14} />}
            {seeding ? 'Seeding…' : 'Seed 25 Items'}
          </button>
          <button className="menu-btn" onClick={loadMenu}><MenuIcon size={14} /> Menu</button>
        </div>
      </header>

      {/* ── SPLIT PANES ────────────────────────────────────────── */}
      <div className="demo-split">
        {/* ── LEFT: WhatsApp Mock ──────────────────────────────── */}
        <div className="pane pane-left">
          <div className="phone-header">
            <Smartphone size={16} />
            <span>WhatsApp · Spice Route QSR</span>
            <span className="online-dot" />
          </div>

          <div className="chat-area">
            {messages.map((m, i) => (
              <ChatBubble key={i} role={m.role} text={m.text} time={m.time} />
            ))}

            {loading && (
              <div className="chat-bubble-wrap chat-bot">
                <div className="chat-bubble bubble-bot typing-indicator">
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* suggestions */}
          <div className="suggestion-row">
            {SUGGESTIONS.map((s, i) => (
              <button key={i} className="chip" onClick={() => handleSend(s)}>{s}</button>
            ))}
          </div>

          {/* input */}
          <div className="chat-input-bar">
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message…"
              disabled={loading}
            />
            <button onClick={() => handleSend()} disabled={loading || !input.trim()}>
              {loading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>

        {/* ── RIGHT: Trace Log ─────────────────────────────────── */}
        <div className="pane pane-right">
          <div className="terminal-header">
            <Terminal size={16} />
            <span>Agent Trace Log</span>
            <span className="terminal-dots">
              <i style={{ background: '#ef4444' }} />
              <i style={{ background: '#eab308' }} />
              <i style={{ background: '#22c55e' }} />
            </span>
          </div>

          <div className="trace-area">
            {traceEntries.length === 0 && (
              <div className="trace-empty">
                <Bot size={40} strokeWidth={1.2} />
                <p>Send a message to see the agent's<br /><strong>Think → Plan → Act → Review → Update</strong> loop</p>
              </div>
            )}

            {traceEntries.map((entry, i) => (
              <TraceEntry key={i} entry={entry} index={i} visible={i < visibleCount} />
            ))}
            <div ref={traceEndRef} />
          </div>
        </div>
      </div>

      {/* ── MENU MODAL ─────────────────────────────────────────── */}
      {showMenu && (
        <div className="modal-overlay" onClick={() => setShowMenu(false)}>
          <div className="menu-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2><ChefHat size={20} /> Menu — Spice Route QSR</h2>
              <button onClick={() => setShowMenu(false)}>✕</button>
            </div>
            <div className="modal-body">
              {menuItems.length === 0 ? (
                <p className="empty-menu">No items yet. Click <strong>Seed 25 Items</strong> first.</p>
              ) : (
                Object.entries(
                  menuItems.reduce((acc, item) => {
                    (acc[item.category] = acc[item.category] || []).push(item);
                    return acc;
                  }, {})
                ).map(([cat, items]) => (
                  <div key={cat} className="menu-category">
                    <h3>{cat}</h3>
                    <div className="menu-grid">
                      {items.map(item => (
                        <div key={item.item_id} className="menu-card">
                          <div className="menu-card-top">
                            <span className="menu-name">{item.name}</span>
                            <span className="menu-price">₹{item.price}</span>
                          </div>
                          <p className="menu-desc">{item.description}</p>
                          {!item.available && <span className="menu-oos">Out of Stock</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
