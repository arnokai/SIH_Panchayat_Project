import { useState, useEffect, useRef, useCallback } from "react";
import { sendAIChatMessage } from "../services/api";

export default function TerraChatBot({ data, selectedCrop = "paddy", activePanchayat }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [speakingIndex, setSpeakingIndex] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const panchayatName = data?.panchayat_name || activePanchayat?.panchayat_name || "Your Panchayat";
  const blockName = data?.block_name || activePanchayat?.block_name || "";
  const districtName = data?.district_name || activePanchayat?.district_name || "West Bengal";
  const cropDisplay = (selectedCrop || "crop").charAt(0).toUpperCase() + (selectedCrop || "crop").slice(1);

  // Today's weather snippet
  const todayForecast = data?.forecast?.[0];
  const todayRainP50 = todayForecast?.rainfall_p50_mm ?? 0;
  const todayRainProb = todayForecast?.prob_rain_pct ?? 0;
  const todayTmax = todayForecast?.temp_max_c ?? 31;

  // Initialize or reset welcome message when Panchayat or Crop changes
  useEffect(() => {
    const welcomeText = (
      `Hello! I am **TerraMind AI**, your dedicated agro-climatic intelligence assistant. ` +
      `I am actively monitoring **${panchayatName}**${blockName ? ` (${blockName} Block)` : ""}, ${districtName} for **${cropDisplay}**.\n\n` +
      `Today's median rainfall is **${todayRainP50.toFixed(1)} mm** (${todayRainProb}% probability) with a high of **${todayTmax.toFixed(1)}°C**.\n\n` +
      `How can I assist your field operations today?`
    );

    const defaultSuggestions = [
      `Can I spray pesticides on my ${cropDisplay} today?`,
      `Should I irrigate my ${cropDisplay} field this week?`,
      `What is the 3-day rainfall and temperature outlook?`,
      `Is there any cyclone or storm danger right now?`,
      `What diseases and pests should I monitor for ${cropDisplay}?`,
    ];

    setMessages([
      {
        role: "assistant",
        content: welcomeText,
        sources: ["TerraMind Agro-Climatic Intelligence", "IMD GKMS", "State Agriculture Dept."],
        action_items: [
          `Review downscaled 5-day rainfall for ${panchayatName}`,
          `Check crop-specific disease alerts for ${cropDisplay}`,
        ],
        suggested_questions: defaultSuggestions,
        engine: "terramind_expert",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  }, [panchayatName, blockName, districtName, cropDisplay, todayRainP50, todayRainProb, todayTmax]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (isOpen && !isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isMinimized]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, isMinimized]);

  // Clean up speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Build telemetry context from current frontend state
  const buildCurrentContext = useCallback(() => {
    const liveCurr = data?.live_weather?.current;
    return {
      panchayat_id: data?.panchayat_id || activePanchayat?.panchayat_id || "WB_107778",
      panchayat_name: panchayatName,
      block_name: blockName,
      district_name: districtName,
      latitude: data?.latitude || activePanchayat?.latitude,
      longitude: data?.longitude || activePanchayat?.longitude,
      elevation_m: data?.elevation_m ?? 15.0,
      soil_type: data?.soil_type || "non_sandy",
      distance_to_river_km: data?.distance_to_river_m ? data.distance_to_river_m / 1000 : null,
      crop: selectedCrop,
      crop_stage: data?.phenology?.stage_name || "Vegetative",
      today_weather: {
        rain_p50: todayRainP50,
        rain_p10: todayForecast?.rainfall_p10_mm ?? 0,
        rain_p90: todayForecast?.rainfall_p90_mm ?? 0,
        prob_rain: todayRainProb,
        temp_max_c: todayTmax,
        temp_min_c: todayForecast?.temp_min_c ?? 24,
        humidity: liveCurr?.relative_humidity_pct ?? 78,
        wind: liveCurr?.wind_speed_kmh ?? 11,
      },
      forecast_summary: data?.forecast || [],
      advisories: data?.advisories || [],
    };
  }, [data, activePanchayat, panchayatName, blockName, districtName, selectedCrop, todayForecast, todayRainP50, todayRainProb, todayTmax]);

  const handleSendMessage = async (queryText) => {
    const text = (queryText || input).trim();
    if (!text || loading) return;

    const userMsg = {
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    try {
      const historyPayload = newHistory.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const contextPayload = buildCurrentContext();
      const response = await sendAIChatMessage(text, historyPayload, contextPayload);

      const assistantMsg = {
        role: "assistant",
        content: response.reply,
        sources: response.sources || [],
        action_items: response.action_items || [],
        suggested_questions: response.suggested_questions || [],
        engine: response.engine || "terramind_expert",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error("AI Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I apologize, but I encountered an error retrieving live agricultural intelligence. Please try asking again in a moment.",
          sources: ["System Failover"],
          action_items: ["Verify network connectivity", "Retry inquiry"],
          suggested_questions: ["Can I spray pesticides today?", "What is today's rain forecast?"],
          engine: "error",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeech = (text, idx) => {
    if (!window.speechSynthesis) return;

    if (speakingIndex === idx) {
      window.speechSynthesis.cancel();
      setSpeakingIndex(null);
      return;
    }

    window.speechSynthesis.cancel();

    // Clean markdown symbols for natural speech
    const cleanText = text
      .replace(/[#*`_~]/g, "")
      .replace(/☑/g, "")
      .replace(/\n+/g, ". ");

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "en-IN";
    utterance.rate = 1.0;

    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => setSpeakingIndex(null);

    setSpeakingIndex(idx);
    window.speechSynthesis.speak(utterance);
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard?.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleClearChat = () => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    setSpeakingIndex(null);
    setMessages([
      {
        role: "assistant",
        content: `Chat history cleared. Monitoring **${panchayatName}** for **${cropDisplay}**. What would you like to know?`,
        sources: ["TerraMind Agro-Climatic Intelligence"],
        action_items: [],
        suggested_questions: [
          `Can I spray pesticides on my ${cropDisplay} today?`,
          `Should I irrigate my ${cropDisplay} field this week?`,
          `What is the 3-day rainfall outlook?`,
        ],
        engine: "terramind_expert",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  };

  // Helper to render markdown-like formatting simply
  const renderFormattedContent = (content) => {
    const lines = content.split("\n");
    return lines.map((line, lIdx) => {
      const trimmed = line.trim();
      if (!trimmed) {
        return <div key={lIdx} className="chat-line-break" />;
      }

      if (trimmed.startsWith("### ")) {
        return (
          <h4 key={lIdx} className="chat-heading-3">
            {trimmed.replace("### ", "")}
          </h4>
        );
      }
      if (trimmed.startsWith("#### ")) {
        return (
          <h5 key={lIdx} className="chat-heading-4">
            {trimmed.replace("#### ", "")}
          </h5>
        );
      }
      if (trimmed.startsWith("- ☑ ") || trimmed.startsWith("- [x] ") || trimmed.startsWith("- ")) {
        const itemText = trimmed.replace(/^-\s*(☑|\[x\])?\s*/, "");
        return (
          <div key={lIdx} className="chat-bullet-row">
            <span className="chat-bullet-icon">☑</span>
            <span className="chat-bullet-text">{itemText}</span>
          </div>
        );
      }

      // Format bold text **text**
      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <p key={lIdx} className="chat-paragraph">
          {parts.map((p, pIdx) => {
            if (p.startsWith("**") && p.endsWith("**")) {
              return <strong key={pIdx}>{p.slice(2, -2)}</strong>;
            }
            return p;
          })}
        </p>
      );
    });
  };

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          className="terra-chat-floating-trigger"
          onClick={() => setIsOpen(true)}
          aria-label="Open TerraMind AI Assistant"
          title="Open TerraMind AI Agro-Climatic Assistant"
        >
          <div className="trigger-pulse-ring"></div>
          <span className="trigger-icon">🤖</span>
          <span className="trigger-label">Ask TerraMind AI</span>
          <span className="trigger-status-dot" title="Online & Context Aware"></span>
        </button>
      )}

      {/* Floating Chat Modal */}
      {isOpen && (
        <aside
          className={`terra-chat-window ${isMinimized ? "minimized" : ""}`}
          aria-label="TerraMind AI Assistant Chat Window"
        >
          {/* Header */}
          <header className="chat-window-header">
            <div className="chat-header-identity">
              <div className="chat-avatar-badge">🤖</div>
              <div>
                <div className="chat-header-title-row">
                  <span className="chat-header-title">TerraMind AI Assistant</span>
                  <span className="chat-active-badge">● Active</span>
                </div>
                <div className="chat-header-subtitle">Panchayat-Scale Agro-Intelligence</div>
              </div>
            </div>

            <div className="chat-header-actions">
              <button
                className="chat-header-btn"
                onClick={handleClearChat}
                title="Clear Conversation"
                aria-label="Clear Conversation"
              >
                🗑️
              </button>
              <button
                className="chat-header-btn"
                onClick={() => setIsMinimized((prev) => !prev)}
                title={isMinimized ? "Expand Chat" : "Minimize Chat"}
                aria-label={isMinimized ? "Expand Chat" : "Minimize Chat"}
              >
                {isMinimized ? "🗖" : "🗕"}
              </button>
              <button
                className="chat-header-btn close-btn"
                onClick={() => {
                  setIsOpen(false);
                  setIsMinimized(false);
                  if (window.speechSynthesis) window.speechSynthesis.cancel();
                  setSpeakingIndex(null);
                }}
                title="Close Assistant"
                aria-label="Close Assistant"
              >
                ✕
              </button>
            </div>
          </header>

          {/* Collapsible Body */}
          {!isMinimized && (
            <>
              {/* Context Telemetry Bar */}
              <div className="chat-context-bar">
                <div className="context-chip">
                  <span className="context-icon">📍</span>
                  <span className="context-val">{panchayatName}</span>
                </div>
                <div className="context-chip">
                  <span className="context-icon">🌾</span>
                  <span className="context-val">{cropDisplay}</span>
                </div>
                <div className="context-chip">
                  <span className="context-icon">🌧️</span>
                  <span className="context-val">{todayRainP50.toFixed(1)} mm</span>
                </div>
              </div>

              {/* Message List */}
              <div className="chat-messages-container">
                {messages.map((msg, idx) => {
                  const isUser = msg.role === "user";
                  return (
                    <div key={idx} className={`chat-message-wrapper ${isUser ? "user" : "assistant"}`}>
                      {!isUser && <div className="chat-msg-avatar">🤖</div>}

                      <div className="chat-bubble">
                        <div className="chat-bubble-body">{renderFormattedContent(msg.content)}</div>

                        {/* Operational Checklist Cards */}
                        {!isUser && msg.action_items && msg.action_items.length > 0 && (
                          <div className="chat-action-checklist-box">
                            <div className="checklist-box-title">📋 Actionable Operations:</div>
                            {msg.action_items.map((act, aIdx) => (
                              <div key={aIdx} className="checklist-box-item">
                                <span className="chk-mark">✓</span>
                                <span>{act}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Authoritative Source Badges */}
                        {!isUser && msg.sources && msg.sources.length > 0 && (
                          <div className="chat-sources-row">
                            <span className="source-label">Sources:</span>
                            {msg.sources.map((src, sIdx) => (
                              <span key={sIdx} className="source-badge">
                                🏛️ {src}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Footer & Actions */}
                        <div className="chat-bubble-footer">
                          <span className="chat-timestamp">{msg.timestamp}</span>

                          {!isUser && (
                            <div className="chat-bubble-actions">
                              <button
                                className={`bubble-action-btn ${speakingIndex === idx ? "active" : ""}`}
                                onClick={() => handleSpeech(msg.content, idx)}
                                title={speakingIndex === idx ? "Stop Audio" : "Listen in English"}
                                aria-label="Listen in English"
                              >
                                {speakingIndex === idx ? "⏹️ Stop" : "🔊 Listen"}
                              </button>
                              <button
                                className="bubble-action-btn"
                                onClick={() => handleCopy(msg.content, idx)}
                                title="Copy response"
                                aria-label="Copy response"
                              >
                                {copiedIndex === idx ? "✓ Copied" : "📋 Copy"}
                              </button>
                            </div>
                          )}
                        </div>

                        {/* Dynamic Suggested Questions */}
                        {!isUser && idx === messages.length - 1 && msg.suggested_questions && msg.suggested_questions.length > 0 && (
                          <div className="chat-suggestions-container">
                            <div className="suggestions-label">💡 Suggested Questions:</div>
                            <div className="suggestions-scroll">
                              {msg.suggested_questions.map((q, qIdx) => (
                                <button
                                  key={qIdx}
                                  className="suggestion-chip"
                                  onClick={() => handleSendMessage(q)}
                                  disabled={loading}
                                >
                                  {q}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Loading typing indicator */}
                {loading && (
                  <div className="chat-message-wrapper assistant">
                    <div className="chat-msg-avatar">🤖</div>
                    <div className="chat-bubble loading-bubble">
                      <div className="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      <span className="typing-text">Analyzing micro-climate &amp; ICAR advisories...</span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Form */}
              <form
                className="chat-input-bar"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
              >
                <input
                  ref={inputRef}
                  type="text"
                  className="chat-text-input"
                  placeholder="Ask about spraying, irrigation, weather, cyclone..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                  aria-label="Your question to TerraMind AI"
                />
                <button
                  type="submit"
                  className="chat-send-btn"
                  disabled={!input.trim() || loading}
                  aria-label="Send message"
                  title="Send message"
                >
                  ➤
                </button>
              </form>
            </>
          )}
        </aside>
      )}
    </>
  );
}
