import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Wrench, FileText, Settings, History, CheckCircle2, AlertCircle, ChevronDown, ChevronUp, Terminal } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'transcripts' | 'config'
  const [provider, setProvider] = useState('openai');
  const [version, setVersion] = useState('baseline');
  
  // Chat state
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Xin chào! Tôi là Research Agent của bạn. Tôi có thể thực hiện tìm kiếm web (Tavily/Firecrawl), tra cứu thông tin và tổng hợp dữ liệu. Bạn cần tôi giúp gì hôm nay?',
      toolEvents: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedTrace, setExpandedTrace] = useState({});
  const messagesEndRef = useRef(null);

  // Config & Metadata
  const [config, setConfig] = useState(null);
  const [transcripts, setTranscripts] = useState([]);
  const [selectedTranscript, setSelectedTranscript] = useState(null);

  useEffect(() => {
    fetchConfig();
    fetchTranscripts();
  }, [version]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchConfig = async () => {
    try {
      const res = await fetch(`/api/config?version=${version}`);
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (err) {
      console.error("Error fetching config:", err);
    }
  };

  const fetchTranscripts = async () => {
    try {
      const res = await fetch('/api/transcripts');
      if (res.ok) {
        const data = await res.json();
        setTranscripts(data);
      }
    } catch (err) {
      console.error("Error fetching transcripts:", err);
    }
  };

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    
    // Append user message
    const updatedMessages = [...messages, { role: 'user', text: userText }];
    setMessages(updatedMessages);
    setLoading(true);

    // Build conversation history for API
    const historyPayload = updatedMessages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({ role: m.role, content: m.text }));

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_input: userText,
          provider: provider,
          version: version,
          history: historyPayload,
          history_window: 5,
          max_tool_rounds: 4
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Lỗi kết nối từ server');
      }

      const data = await res.json();
      
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: data.assistant_text || 'Đã nhận kết quả từ các tools.',
          toolEvents: data.tool_events || [],
          rounds: data.rounds || [],
          status: data.status,
          artifactVersion: data.artifact_version
        }
      ]);

      // Refresh transcripts list
      fetchTranscripts();
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: `❌ Lỗi: ${err.message}`,
          isError: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleTrace = (index) => {
    setExpandedTrace(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const loadTranscriptDetails = async (transcriptId) => {
    try {
      const res = await fetch(`/api/transcripts/${transcriptId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedTranscript(data);
      }
    } catch (err) {
      console.error("Error loading transcript details:", err);
    }
  };

  return (
    <div className="app-container">
      {/* Top Navigation Header */}
      <header className="app-header">
        <div className="brand-logo">
          <div className="brand-icon">RA</div>
          <div>
            <div className="brand-title">Research Agent Studio</div>
            <div className="brand-subtitle">Day 04 Lab — Evidence-Driven AI Agent</div>
          </div>
        </div>

        <div className="header-controls">
          <div className="control-group">
            <span className="control-label">Provider:</span>
            <select 
              className="control-select" 
              value={provider} 
              onChange={(e) => setProvider(e.target.value)}
            >
              <option value="openai">OpenAI (GPT-4o)</option>
              <option value="openrouter">OpenRouter</option>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="gemini">Google Gemini</option>
            </select>
          </div>

          <div className="control-group">
            <span className="control-label">Version:</span>
            <select 
              className="control-select" 
              value={version} 
              onChange={(e) => setVersion(e.target.value)}
            >
              <option value="baseline">baseline</option>
              <option value="v1">v1</option>
              <option value="v2">v2</option>
              <option value="v3">v3</option>
            </select>
          </div>

          <div className="version-badge">
            <span className="version-dot"></span>
            {config?.artifact_version ? config.artifact_version.slice(0, 18) : version}
          </div>
        </div>
      </header>

      {/* Tabs Menu */}
      <div className="tabs-bar">
        <button 
          className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <Bot size={18} /> Chat Studio
        </button>
        <button 
          className={`tab-btn ${activeTab === 'transcripts' ? 'active' : ''}`}
          onClick={() => setActiveTab('transcripts')}
        >
          <History size={18} /> Transcripts & Log Runs ({transcripts.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'config' ? 'active' : ''}`}
          onClick={() => setActiveTab('config')}
        >
          <Settings size={18} /> Prompts & Tools Config
        </button>
      </div>

      {/* Main Body */}
      <div className="main-body">
        {activeTab === 'chat' && (
          <div className="chat-section">
            <div className="messages-container">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message-bubble ${msg.role}`}>
                  <div className={`avatar ${msg.role === 'user' ? 'user-avatar' : 'ai-avatar'}`}>
                    {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </div>

                  <div className="message-content">
                    <div>{msg.text}</div>

                    {/* Tool Execution Trace Card */}
                    {msg.toolEvents && msg.toolEvents.length > 0 && (
                      <div className="tool-trace-card">
                        <div className="tool-trace-header" onClick={() => toggleTrace(idx)}>
                          <div className="tool-trace-title">
                            <Wrench size={15} />
                            <span>Đã thực thi {msg.toolEvents.length} công cụ (Tool Call Trace)</span>
                          </div>
                          {expandedTrace[idx] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </div>

                        {expandedTrace[idx] && (
                          <div className="tool-trace-body">
                            {msg.toolEvents.map((evt, eIdx) => (
                              <div key={eIdx} style={{ marginBottom: '10px' }}>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                                  <span className="tool-badge">🔧 {evt.tool}</span>
                                  <span style={{ fontSize: '0.75rem', color: '#718096' }}>
                                    Args: {JSON.stringify(evt.args)}
                                  </span>
                                </div>
                                <div className="code-block">
                                  {JSON.stringify(evt.result, null, 2)}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-bubble assistant">
                  <div className="avatar ai-avatar">
                    <Bot size={18} />
                  </div>
                  <div className="message-content" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#68d391', animation: 'ping 1s infinite' }}></div>
                    <span>Agent đang suy nghĩ & gọi tool...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <form className="chat-input-area" onSubmit={handleSend}>
              <div className="input-wrapper">
                <input 
                  type="text" 
                  className="chat-input"
                  placeholder="Nhập yêu cầu cho Research Agent (ví dụ: 'Tìm bài viết về AI trên ví dụ example.com')..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                />
                <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
                  <Send size={18} />
                </button>
              </div>
            </form>
          </div>
        )}

        {activeTab === 'transcripts' && (
          <div style={{ display: 'flex', flex: 1, padding: '24px', gap: '24px', overflow: 'hidden' }}>
            <div style={{ width: '380px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Danh sách Transcripts</h3>
              <div className="transcript-list" style={{ flex: 1, overflowY: 'auto' }}>
                {transcripts.map((t) => (
                  <div 
                    key={t.transcript_id} 
                    className="transcript-item"
                    onClick={() => loadTranscriptDetails(t.transcript_id)}
                    style={{
                      borderColor: selectedTranscript?.transcript_id === t.transcript_id ? '#68d391' : '#e2e8f0',
                      backgroundColor: selectedTranscript?.transcript_id === t.transcript_id ? '#e6fffa' : '#ffffff'
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{t.transcript_id}</div>
                    <div className="transcript-meta">
                      <span>Provider: {t.provider}</span>
                      <span>{t.turns_count} lượt</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ flex: 1, backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', overflowY: 'auto' }}>
              {selectedTranscript ? (
                <div>
                  <h3 style={{ marginBottom: '12px', color: '#1a202c' }}>Chi tiết Transcript: {selectedTranscript.transcript_id}</h3>
                  <div style={{ fontSize: '0.85rem', color: '#718096', marginBottom: '16px' }}>
                    Tạo lúc: {selectedTranscript.created_at} | Provider: {selectedTranscript.provider} | Version: {selectedTranscript.artifact_version}
                  </div>

                  <h4 style={{ margin: '16px 0 8px' }}>Các lượt hội thoại (Turns):</h4>
                  {selectedTranscript.turns?.map((turn, tIdx) => (
                    <div key={tIdx} style={{ background: '#f7fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px', marginBottom: '12px' }}>
                      <div style={{ fontWeight: 700, color: '#2b6cb0' }}>Turn #{turn.turn_index}: {turn.user}</div>
                      <div style={{ marginTop: '8px', fontSize: '0.9rem' }}>Agent: {turn.assistant_text}</div>

                      {turn.tool_events && turn.tool_events.length > 0 && (
                        <div style={{ marginTop: '10px' }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#4a5568' }}>Tools đã dùng:</div>
                          {turn.tool_events.map((te, teIdx) => (
                            <div key={teIdx} className="code-block" style={{ marginTop: '4px' }}>
                              {te.tool}({JSON.stringify(te.args)}) {"=>"} {JSON.stringify(te.result)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: '#a0aec0', display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                  Chọn một Transcript bên trái để xem thông tin chi tiết.
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'config' && (
          <div style={{ flex: 1, padding: '24px', display: 'flex', gap: '24px', overflow: 'hidden' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <h3 style={{ marginBottom: '12px', fontSize: '1rem', fontWeight: 700 }}>System Prompt (`artifacts/system_prompt.md`)</h3>
              <div className="code-block" style={{ flex: 1, overflowY: 'auto' }}>
                {config?.system_prompt || 'Chưa tải được system prompt.'}
              </div>
            </div>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <h3 style={{ marginBottom: '12px', fontSize: '1rem', fontWeight: 700 }}>Khai báo Tools (`artifacts/tools.yaml`)</h3>
              <div className="code-block" style={{ flex: 1, overflowY: 'auto' }}>
                {JSON.stringify(config?.tools || [], null, 2)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
