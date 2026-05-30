import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../variables/context/AuthContext';
import { chatAPI } from '../variables/services/api';
import api from '../variables/services/api';
import styles from './Chat.module.css';

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function generateThreadId(userId) {
  return `${userId}-${Math.random().toString(36).slice(2, 10)}`;
}

// ── Message Bubble ────────────────────────────────────────
function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  const isSystem = msg.role === 'system';

  if (isSystem) {
    return (
      <div className={styles.systemMsg}>
        <span>{msg.content}</span>
      </div>
    );
  }

  return (
    <div className={`${styles.bubble} ${isUser ? styles.userBubble : styles.aiBubble}`}>
      {!isUser && (
        <div className={styles.avatar}>
          <span>CP</span>
        </div>
      )}
      <div className={`${styles.bubbleContent} ${isUser ? styles.userContent : styles.aiContent}`}>
        <div className={styles.text}>
          {isUser ? (
            <>
              {msg.content}
              {msg.streaming && <span className={styles.cursor} />}
            </>
          ) : (
            <>
              <ReactMarkdown
                components={{
                  a: ({ node, children, ...props }) => (
                    <a {...props} target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                }}
              >
                {msg.content || ''}
              </ReactMarkdown>
              {msg.streaming && <span className={styles.cursor} />}
            </>
          )}
        </div>
        <div className={styles.timestamp}>{msg.time}</div>
      </div>
      {isUser && (
        <div className={`${styles.avatar} ${styles.userAvatar}`}>
          <span>U</span>
        </div>
      )}
    </div>
  );
}

// ── Approval Card ─────────────────────────────────────────
function ApprovalCard({ onApprove, onReject }) {
  return (
    <div className={styles.approvalCard}>
      <div className={styles.approvalIcon}>⚠️</div>
      <div className={styles.approvalText}>
        <p className={styles.approvalTitle}>Action requires confirmation</p>
        <p className={styles.approvalSub}>The assistant wants to perform a sensitive action.</p>
      </div>
      <div className={styles.approvalBtns}>
        <button className={styles.approveBtn} onClick={onApprove}>Approve</button>
        <button className={styles.rejectBtn} onClick={onReject}>Reject</button>
      </div>
    </div>
  );
}

// ── Icons ─────────────────────────────────────────────────
function FileIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}

function PaperclipIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  );
}

// ── Main Chat Component ───────────────────────────────────
export default function Chat() {
  const { user, logout } = useAuth();

  const initialMessage = {
    id: 1,
    role: 'assistant',
    content: `Hi ${user?.name?.split(' ')[0] || 'there'}! I'm CareerPal — your AI assistant for job hunting, emails, and career growth. How can I help you today?`,
    time: now(),
  };

  const [messages, setMessages] = useState([initialMessage]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showApproval, setShowApproval] = useState(false);
  const [status, setStatus] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // session state
  const [sessions, setSessions] = useState([]);
  const [threadId, setThreadId] = useState(() => generateThreadId(user?.id || 'user'));
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const bottomRef = useRef(null);
  const fileRef = useRef(null);
  const inputRef = useRef(null);

  // auto scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, status]);

  // load sessions on mount
  useEffect(() => {
    if (user?.id) loadSessions();
  }, [user?.id]);

  // ── Session operations ────────────────────────────────
  const loadSessions = async () => {
    setSessionsLoading(true);
    try {
      const res = await api.get(`/api/sessions/${user.id}`);
      setSessions(res.data.sessions || []);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setSessionsLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const res = await api.post('/api/sessions/', { user_id: user.id });
      const newThreadId = res.data.thread_id;

      setThreadId(newThreadId);
      setMessages([initialMessage]);
      setInput('');
      setFile(null);
      setStatus('');

      // add new session to top of list immediately (optimistic update)
      setSessions(prev => [{
        thread_id:    newThreadId,
        title:        'New Chat',
        last_message: '',
        created_at:   new Date().toISOString(),
      }, ...prev]);

    } catch (err) {
      console.error('Failed to create session:', err);
      // fallback — create thread id locally
      const newThreadId = generateThreadId(user?.id || 'user');
      setThreadId(newThreadId);
      setMessages([initialMessage]);
    }
  };

  const handleLoadSession = async (session) => {
    setThreadId(session.thread_id);
    setStatus('');

    // load message history from backend
    try {
      const res = await api.get(`/api/sessions/${session.thread_id}/messages`);
      const history = res.data.messages || [];

      if (history.length > 0) {
        setMessages(history.map((m, i) => ({
          id: i + 1,
          role: m.role,
          content: m.content,
          time: now(),
        })));
      } else {
        setMessages([initialMessage]);
      }
    } catch (err) {
      console.error('Failed to load session messages:', err);
      setMessages([initialMessage]);
    }
  };

  const handleDeleteSession = async (e, threadIdToDelete) => {
    e.stopPropagation(); // prevent triggering handleLoadSession
    try {
      await api.delete(`/api/sessions/${threadIdToDelete}`);
      setSessions(prev => prev.filter(s => s.thread_id !== threadIdToDelete));

      // if deleted current session → create new one
      if (threadIdToDelete === threadId) {
        handleNewChat();
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  // ── Message operations ────────────────────────────────
  const addMessage = useCallback((msg) => {
    setMessages(prev => [...prev, { id: Date.now() + Math.random(), time: now(), ...msg }]);
  }, []);

  const updateLastAI = useCallback((content, streaming = true) => {
    setMessages(prev => {
      const copy = [...prev];
      const last = copy[copy.length - 1];
      if (last?.role === 'assistant') {
        copy[copy.length - 1] = { ...last, content, streaming };
      }
      return copy;
    });
  }, []);

  // update session title after first message
  const updateSessionTitle = useCallback((userMessage) => {
    setSessions(prev => prev.map(s =>
      s.thread_id === threadId
        ? { ...s, title: userMessage.slice(0, 40) + (userMessage.length > 40 ? '...' : ''), last_message: userMessage }
        : s
    ));
  }, [threadId]);

  const handleSend = async () => {
    if ((!input.trim() && !file) || loading) return;

    const userMsg = input.trim();
    const userFile = file;
    setInput('');
    setFile(null);
    setStatus('');

    addMessage({
      role: 'user',
      content: userMsg || '(file uploaded)',
      file: userFile?.name || null,
    });

    // update sidebar title with first message
    updateSessionTitle(userMsg);

    // placeholder AI message
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'assistant',
      content: '',
      streaming: true,
      time: now(),
    }]);

    setLoading(true);

    try {
      let accumulated = '';

      const onChunk = (chunk) => {
        if (chunk.startsWith('__STATUS__')) {
          setStatus(chunk.replace('__STATUS__', '').trim());
          return;
        }

      // ── Clarification question from backend ──
        if (chunk.startsWith('__CLARIFICATION__')) {
          const question = chunk.replace('__CLARIFICATION__', '').trim();
          // Replace the streaming placeholder with the clarification question
          updateLastAI(question, false);
          setStatus('');
          return;
        }

        const decoded = chunk.replace(/\\n/g, '\n');
        accumulated += decoded;
        updateLastAI(accumulated, true);

        if (accumulated.includes('__APPROVAL_REQUIRED__')) {
          setShowApproval(true);
        }
    };

      if (userFile) {
        await chatAPI.uploadAndChat(userFile, userMsg, threadId, onChunk);
      } else {
        await chatAPI.sendMessage(userMsg, threadId, onChunk);
      }

      updateLastAI(accumulated.replace('__APPROVAL_REQUIRED__', '').trim(), false);
    } catch (err) {
      updateLastAI('Sorry, something went wrong. Please try again.', false);
    } finally {
      setLoading(false);
      setStatus('');
    }
  };

  const handleApprove = async () => {
    setShowApproval(false);
    try {
      await chatAPI.approve(threadId, 'yes');
      addMessage({ role: 'system', content: '✅ Action approved' });
    } catch {
      addMessage({ role: 'system', content: 'Failed to approve action' });
    }
  };

  const handleReject = async () => {
    setShowApproval(false);
    try {
      await chatAPI.approve(threadId, 'no');
      addMessage({ role: 'system', content: '❌ Action rejected' });
    } catch {}
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f) setFile(f);
    e.target.value = '';
  };

  const suggestions = [
    '🔍 Find AI Engineer jobs',
    '📧 Check my inbox',
    '✍️ Help write my resume',
    '💼 Apply to recent jobs',
  ];

  // ── Render ─────────────────────────────────────────────
  return (
    <div className={styles.layout}>

      {/* ── Sidebar ── */}
      <aside className={`${styles.sidebar} ${sidebarOpen ? styles.sidebarOpen : styles.sidebarClosed}`}>
        <div className={styles.sidebarHeader}>
          <div className={styles.logo}>
            <div className={styles.logoIcon}>CP</div>
            {sidebarOpen && <span className={styles.logoText}>CareerPal</span>}
          </div>
          <button className={styles.toggleBtn} onClick={() => setSidebarOpen(o => !o)}>
            {sidebarOpen ? '←' : '→'}
          </button>
        </div>

        {sidebarOpen && (
          <>
            {/* New Chat button */}
            <button className={styles.newChatBtn} onClick={handleNewChat}>
              + New Chat
            </button>

            {/* Sessions list */}
            <div className={styles.sidebarSection}>
              <p className={styles.sidebarLabel}>Recent</p>

              {sessionsLoading && (
                <div className={styles.sessionsLoading}>
                  <span />Loading...
                </div>
              )}

              {!sessionsLoading && sessions.length === 0 && (
                <p className={styles.noSessions}>No sessions yet</p>
              )}

              {sessions.map(session => (
                <div
                  key={session.thread_id}
                  className={`${styles.historyItem} ${session.thread_id === threadId ? styles.activeSession : ''}`}
                  onClick={() => handleLoadSession(session)}
                >
                  <span className={styles.historyTitle}>{session.title}</span>
                  <button
                    className={styles.deleteSessionBtn}
                    onClick={(e) => handleDeleteSession(e, session.thread_id)}
                    title="Delete session"
                  >
                    <TrashIcon />
                  </button>
                </div>
              ))}
            </div>

            {/* User footer */}
            <div className={styles.sidebarFooter}>
              <div className={styles.userInfo}>
                <div className={styles.userAvatar2}>
                  {user?.name?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className={styles.userDetails}>
                  <p className={styles.userName}>{user?.name || 'User'}</p>
                  <p className={styles.userEmail}>{user?.email || ''}</p>
                </div>
              </div>
              <button className={styles.logoutBtn} onClick={logout} title="Sign out">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
              </button>
            </div>
          </>
        )}
      </aside>

      {/* ── Main ── */}
      <main className={styles.main}>

        {/* Messages */}
        <div className={styles.messages}>
          {messages.length === 1 && (
            <div className={styles.welcome}>
              <h2 className={styles.welcomeTitle}>What can I help with?</h2>
              <div className={styles.suggestions}>
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    className={styles.suggestion}
                    onClick={() => { setInput(s.slice(2).trim()); inputRef.current?.focus(); }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}

          {showApproval && (
            <ApprovalCard onApprove={handleApprove} onReject={handleReject} />
          )}

          <div ref={bottomRef} />
        </div>

        {/* Status bar */}
        {status && loading && (
          <div className={styles.statusBar}>
            <div className={styles.statusDots}>
              <span /><span /><span />
            </div>
            <span className={styles.statusText}>{status}</span>
          </div>
        )}

        {/* Input area */}
        <div className={styles.inputArea}>
          {file && (
            <div className={styles.filePreview}>
              <FileIcon />
              <span>{file.name}</span>
              <button className={styles.removeFile} onClick={() => setFile(null)}>×</button>
            </div>
          )}

          <div className={styles.inputRow}>
            <button className={styles.attachBtn} onClick={() => fileRef.current?.click()} title="Attach file">
              <PaperclipIcon />
            </button>
            <input
              ref={fileRef}
              type="file"
              style={{ display: 'none' }}
              onChange={handleFileChange}
              accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
            />
            <textarea
              ref={inputRef}
              className={styles.input}
              placeholder="Message CareerPal..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            <button
              className={`${styles.sendBtn} ${(input.trim() || file) && !loading ? styles.sendActive : ''}`}
              onClick={handleSend}
              disabled={(!input.trim() && !file) || loading}
            >
              {loading ? <span className={styles.spinner} /> : <SendIcon />}
            </button>
          </div>
          <p className={styles.hint}>Press Enter to send · Shift+Enter for new line</p>
        </div>
      </main>
    </div>
  );
}