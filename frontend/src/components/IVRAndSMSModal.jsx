import { useState, useEffect, useRef } from "react";
import { fetchSMSDelivery, fetchIVRDelivery } from "../services/api";

export default function IVRAndSMSModal({ isOpen, onClose, panchayatId, crop = "paddy", lang = "en" }) {
  const [activeTab, setActiveTab] = useState("sms"); // "sms" | "ivr"
  const [smsData, setSmsData] = useState(null);
  const [ivrData, setIvrData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copiedLang, setCopiedLang] = useState(null);
  
  // IVR simulation states
  const [callActive, setCallActive] = useState(false);
  const [activeMenuSelection, setActiveMenuSelection] = useState(null);
  const [audioSpeaking, setAudioSpeaking] = useState(false);
  const synthRef = useRef(null);

  useEffect(() => {
    if (!isOpen || !panchayatId) return;

    setLoading(true);
    Promise.all([
      fetchSMSDelivery(panchayatId, crop).catch(() => null),
      fetchIVRDelivery(panchayatId, crop).catch(() => null),
    ]).then(([smsRes, ivrRes]) => {
      setSmsData(smsRes);
      setIvrData(ivrRes);
      setLoading(false);
    });

    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setCallActive(false);
      setAudioSpeaking(false);
    };
  }, [isOpen, panchayatId, crop]);

  if (!isOpen) return null;

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopiedLang(type);
    setTimeout(() => setCopiedLang(null), 2500);
  };

  const startIVRCall = () => {
    if (!ivrData) return;
    setCallActive(true);
    setActiveMenuSelection(null);

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const textToSpeak = ivrData.script_en || "Welcome to TerraMind toll free climate helpline.";
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.lang = "en-IN";
      utterance.rate = 0.95;

      utterance.onstart = () => setAudioSpeaking(true);
      utterance.onend = () => setAudioSpeaking(false);
      utterance.onerror = () => setAudioSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  };

  const endIVRCall = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setCallActive(false);
    setAudioSpeaking(false);
    setActiveMenuSelection(null);
  };

  const handleDialpadPress = (key) => {
    if (!callActive || !ivrData) return;
    setActiveMenuSelection(key);
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      let responseSpeech = "";
      if (key === "1") {
        responseSpeech = "Today rain probability is active. Optimal spraying window is 7 AM to 10 AM.";
      } else if (key === "2") {
        responseSpeech = `For ${crop}: Keep field drainage bunds open to prevent root inundation.`;
      } else if (key === "3") {
        responseSpeech = "PMFBY weather index verified. Loss certificate generated for this Gram Panchayat.";
      } else {
        responseSpeech = "Connecting you to Block Krishi Sahayak Officer. Please stay on the line.";
      }

      const utterance = new SpeechSynthesisUtterance(responseSpeech);
      utterance.lang = "en-IN";
      utterance.rate = 0.95;
      utterance.onstart = () => setAudioSpeaking(true);
      utterance.onend = () => setAudioSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="ivr-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="ivr-modal-header">
          <div className="ivr-header-title">
            <span className="ivr-header-icon">📡</span>
            <div>
              <h2>Zero-Data Voice & SMS Broadcast</h2>
              <p>160-Character Unicode SMS & Automated 1800-TERRAMIND IVR Hotline</p>
            </div>
          </div>
          <button className="ivr-modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="ivr-tab-bar">
          <button
            className={`ivr-tab-btn ${activeTab === "sms" ? "active" : ""}`}
            onClick={() => setActiveTab("sms")}
          >
            💬 160-Char Action SMS (Feature Phone)
          </button>
          <button
            className={`ivr-tab-btn ${activeTab === "ivr" ? "active" : ""}`}
            onClick={() => setActiveTab("ivr")}
          >
            📞 Toll-Free Missed-Call IVR (1800-TERRAMIND)
          </button>
        </div>

        {loading ? (
          <div className="ivr-modal-loading">
            <span className="trust-spinner"></span>
            <span>Generating localized broadcast payload...</span>
          </div>
        ) : (
          <div className="ivr-modal-body">
            {activeTab === "sms" && smsData && (
              <div className="sms-tab-content">
                <div className="sms-banner-notice">
                  <span>ℹ️</span>
                  <span>
                    Adheres strictly to the handbook rule: <strong>Action First, Reason Second, Number Last</strong>. Single-segment SMS guaranteed (&le; 160 chars) for zero-cost delivery across 2G feature phones.
                  </span>
                </div>

                <div className="sms-cards-grid single-card">
                  {/* English SMS Card */}
                  <div className="sms-message-card full-width">
                    <div className="sms-card-top">
                      <span className="sms-lang-tag">English (Official 160-Char Broadcast)</span>
                      <span className={`sms-char-counter ${smsData.char_count_en <= 160 ? "valid" : "overflow"}`}>
                        {smsData.char_count_en} / 160 chars
                      </span>
                    </div>
                    <div className="sms-screen-box">
                      <p>{smsData.message_en}</p>
                    </div>
                    <div className="sms-card-actions">
                      <button
                        className="sms-copy-btn"
                        onClick={() => handleCopy(smsData.message_en, "en")}
                      >
                        {copiedLang === "en" ? "✓ Copied to Clipboard" : "📋 Copy SMS Broadcast"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "ivr" && ivrData && (
              <div className="ivr-tab-content">
                <div className="ivr-phone-simulator">
                  {/* Phone Screen Mockup */}
                  <div className="phone-chassis">
                    <div className="phone-screen">
                      <div className="phone-status-bar">
                        <span>📶 4G / 2G</span>
                        <span>1800-TERRAMIND</span>
                        <span>🔋 92%</span>
                      </div>
                      
                      <div className="phone-call-display">
                        {callActive ? (
                          <>
                            <div className="call-live-indicator">
                              <span className={`pulse-ring ${audioSpeaking ? "speaking" : ""}`}></span>
                              <span>LIVE TOLL-FREE BROADCAST</span>
                            </div>
                            <div className="phone-gp-name">{ivrData.panchayat_name} PANCHAYAT</div>
                            <div className="phone-audio-status">
                              {audioSpeaking ? "🔊 Playing Voice Advisory..." : "Waiting for keypad input..."}
                            </div>
                            {activeMenuSelection && (
                              <div className="phone-selected-key">
                                Pressed Key: <strong>{activeMenuSelection}</strong>
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="phone-idle-state">
                            <span className="phone-tollfree-large">1800-TERRAMIND</span>
                            <p>Toll-Free Interactive Voice Response Hotline for Rural West Bengal</p>
                            <span className="missed-call-hint">
                              "Farmer gives missed call &rarr; Automated system calls back free"
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Phone Dialpad */}
                      <div className="phone-dialpad">
                        {["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"].map((key) => (
                          <button
                            key={key}
                            className={`dial-btn ${activeMenuSelection === key ? "pressed" : ""}`}
                            onClick={() => handleDialpadPress(key)}
                            disabled={!callActive}
                          >
                            {key}
                          </button>
                        ))}
                      </div>

                      {/* Call Action Button */}
                      <div className="phone-call-actions">
                        {!callActive ? (
                          <button className="phone-start-call-btn" onClick={startIVRCall}>
                            📞 Call 1800-TERRAMIND
                          </button>
                        ) : (
                          <button className="phone-end-call-btn" onClick={endIVRCall}>
                            ⏹️ End Call
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* IVR Voice Script Guide */}
                  <div className="ivr-script-side">
                    <h4>Voice Telephony Script ({lang === "bn" ? "বাংলা" : "English"})</h4>
                    <div className="ivr-script-box">
                      <p>{lang === "bn" ? ivrData.script_bn : ivrData.script_en}</p>
                    </div>

                    <div className="ivr-menu-breakdown">
                      <h5>Interactive Keypad Menu:</h5>
                      <ul>
                        {ivrData.dialpad_menu.map((item) => (
                          <li key={item.key} className={activeMenuSelection === item.key ? "highlight" : ""}>
                            <kbd>{item.key}</kbd>
                            <span>{lang === "bn" ? item.label_bn : item.label_en}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
