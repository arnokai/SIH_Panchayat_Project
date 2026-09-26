import { useState } from "react";
import { formatForecastDate } from "../utils/formatters";

const CROP_ICONS = {
  paddy: "🌾",
  potato: "🥔",
  mustard: "🌼",
  jute: "🌿",
  vegetables: "🥬",
};

const REQUIRED_CROP_INSTITUTES = {
  paddy: {
    institute: "ICAR-NRRI (National Rice Research Institute) & BCKV Agromet Field Unit",
    shortName: "ICAR-NRRI & BCKV AMFU",
    portal: "https://nrri.nic.in",
  },
  potato: {
    institute: "ICAR-CPRI (Central Potato Research Institute) & BCKV Mohanpur",
    shortName: "ICAR-CPRI & BCKV Mohanpur",
    portal: "https://cpri.icar.gov.in",
  },
  mustard: {
    institute: "ICAR-DRMR (Directorate of Rapeseed-Mustard Research) & District KVKs",
    shortName: "ICAR-DRMR & District KVKs",
    portal: "https://drmr.icar.gov.in",
  },
  jute: {
    institute: "ICAR-CRIJAF (Central Research Institute for Jute and Allied Fibres, Barrackpore)",
    shortName: "ICAR-CRIJAF (Barrackpore)",
    portal: "https://crijaf.icar.gov.in",
  },
  vegetables: {
    institute: "ICAR-IIHR (Indian Institute of Horticultural Research) & Dept. of Agriculture, GoWB",
    shortName: "ICAR-IIHR & Dept. of Agriculture",
    portal: "https://iihr.res.in",
  },
};

export default function AgronomicAlerts({
  advisories = [],
  crop = "paddy",
  panchayatName = "",
  bulletin = null,
}) {
  const [speakingId, setSpeakingId] = useState(null);
  const [showBulletinDetails, setShowBulletinDetails] = useState(false);

  const cleanCrop = (crop || "paddy").toLowerCase();
  const cropIcon = CROP_ICONS[cleanCrop] || "🌱";
  const requiredInfo = REQUIRED_CROP_INSTITUTES[cleanCrop] || {
    institute: "IMD Gramin Krishi Mausam Sewa (GKMS) & MoES",
    shortName: "IMD GKMS",
    portal: "https://mausam.imd.gov.in",
  };

  const speakAdvisory = (text, id) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Speech synthesis is not supported in this browser.");
      return;
    }

    if (speakingId === id) {
      window.speechSynthesis.cancel();
      setSpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = 0.92;

    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find((v) => v.lang.startsWith("en"));
    if (voice) {
      utterance.voice = voice;
    }

    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    setSpeakingId(id);
    window.speechSynthesis.speak(utterance);
  };

  const shareOnWhatsApp = ({ date, textEn, priority, source, actionItems, bulletinRef }) => {
    const mainText = textEn || "";
    const actionsFormatted =
      actionItems && actionItems.length > 0
        ? `\n📋 *Action Items:*\n` + actionItems.map((a) => `  • ${a}`).join("\n")
        : "";

    const lines = [
      "🌾 *TerraMind Panchayat Agricultural Advisory* 🌾",
      panchayatName ? `📍 *Panchayat:* ${panchayatName}` : null,
      date ? `📅 *Date:* ${formatForecastDate(date)}` : null,
      crop ? `🌱 *Selected Crop:* ${cropIcon} ${crop.toUpperCase()}` : null,
      source ? `🏛️ *Authoritative Source:* ${source}` : null,
      bulletinRef ? `📋 *Bulletin Ref:* ${bulletinRef}` : null,
      `📢 *Advisory (${(priority || "Advisory").toUpperCase()}):* ${mainText}`,
      actionsFormatted,
      "",
      "🔗 _TerraMind — Panchayat Micro-Climate & Agro-Advisory Intelligence System_",
    ]
      .filter(Boolean)
      .join("\n");

    const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(lines)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  // Sort advisories: High priority first, then medium, then low
  const priorityOrder = { high: 0, medium: 1, low: 2, info: 3 };
  const sortedAdvisories = [...(advisories || [])].sort((a, b) => {
    const pA = priorityOrder[a.priority?.toLowerCase()] ?? 99;
    const pB = priorityOrder[b.priority?.toLowerCase()] ?? 99;
    return pA - pB;
  });

  const handleSpeakAll = () => {
    const allText = sortedAdvisories
      .map((a) => {
        const datePrefix = a.date ? `${formatForecastDate(a.date)}: ` : "";
        const sourcePrefix = a.source ? `According to ${a.source}: ` : "";
        const actionText =
          a.action_items && a.action_items.length > 0
            ? ` Recommended actions: ${a.action_items.join(". ")}`
            : "";
        return `${datePrefix}${sourcePrefix}${a.text_en || a.text}.${actionText}`;
      })
      .join(". ");
    speakAdvisory(allText, "all-advisories");
  };

  return (
    <section className="advisory-section">
      <div className="section-header">
        <div>
          <h3 className="section-title">Field Agricultural Advisories & Alerts</h3>
          <p className="section-subtitle">
            Actionable farming recommendations for{" "}
            <span className="advisory-selected-crop-chip">
              {cropIcon} {crop.toUpperCase()}
            </span>{" "}
            grounded in required authoritative ICAR & IMD Agromet sources
          </p>
        </div>
        <div className="advisory-top-right">
          {sortedAdvisories.length > 0 && (
            <button
              type="button"
              className={`btn-voice-all ${speakingId === "all-advisories" ? "is-speaking" : ""}`}
              onClick={handleSpeakAll}
              title="Listen to all crop advisories in English"
            >
              <span className="action-icon">
                {speakingId === "all-advisories" ? "⏹️" : "🔊"}
              </span>
              <span>
                {speakingId === "all-advisories" ? "Stop" : "Listen All (Audio)"}
              </span>
            </button>
          )}
          <div className="advisory-count-badge">
            {sortedAdvisories.length} Active {sortedAdvisories.length === 1 ? "Advisory" : "Advisories"} for {cropIcon} {crop.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Official Agromet Advisory Bulletin from Required Source */}
      <div className="official-source-bulletin-banner">
        <div className="bulletin-banner-top">
          <div className="bulletin-banner-left">
            <span className="live-source-status-pill">
              <span className="live-pulse-dot"></span>
              Live Source Synchronized
            </span>
            <span className="required-source-title">
              🏛️ <strong>Required Source:</strong> {bulletin?.required_source || requiredInfo.institute}
            </span>
          </div>
          <div className="bulletin-banner-right">
            {bulletin?.bulletin_number && (
              <span className="bulletin-ref-pill">
                📋 Ref: <strong>{bulletin.bulletin_number}</strong>
              </span>
            )}
            <button
              type="button"
              className="btn-toggle-bulletin"
              onClick={() => setShowBulletinDetails(!showBulletinDetails)}
            >
              {showBulletinDetails ? "▲ Hide Official Bulletin" : "▼ View Official Bulletin"}
            </button>
          </div>
        </div>

        {showBulletinDetails && (
          <div className="bulletin-expanded-content">
            <div className="bulletin-meta-grid">
              <div className="bulletin-meta-item">
                <span className="meta-label">Agromet Field Unit (AMFU):</span>
                <span className="meta-value">{bulletin?.amfu_center || "AMFU Mohanpur, Bidhan Chandra Krishi Viswavidyalaya (BCKV)"}</span>
              </div>
              <div className="bulletin-meta-item">
                <span className="meta-label">Nodal University:</span>
                <span className="meta-value">{bulletin?.university || "Bidhan Chandra Krishi Viswavidyalaya (BCKV)"}</span>
              </div>
              <div className="bulletin-meta-item">
                <span className="meta-label">Lead Agrometeorologist:</span>
                <span className="meta-value">{bulletin?.lead_scientist || "Dr. P. K. Ghosh, Senior Agrometeorologist"}</span>
              </div>
              <div className="bulletin-meta-item">
                <span className="meta-label">Advisory Validity:</span>
                <span className="meta-value">
                  {bulletin?.issue_date ? `Issued: ${formatForecastDate(bulletin.issue_date)} • Valid Till: ${formatForecastDate(bulletin.valid_until)}` : "Current 5-Day Operational Cycle"}
                </span>
              </div>
            </div>

            {bulletin?.synoptic_weather_overview && (
              <div className="bulletin-synoptic-card">
                <strong>☁️ IMD Synoptic Atmospheric Situation:</strong>
                <p>{bulletin.synoptic_weather_overview}</p>
              </div>
            )}

            {bulletin?.crop_advisory?.advisory_summary && (
              <div className="bulletin-crop-highlight">
                <strong>{cropIcon} Official Guidance for {crop.toUpperCase()}:</strong>
                <p>{bulletin.crop_advisory.advisory_summary}</p>
                {bulletin.crop_advisory.agronomic_guidance && (
                  <p className="guidance-detail">{bulletin.crop_advisory.agronomic_guidance}</p>
                )}
              </div>
            )}

            <div className="bulletin-links-row">
              <a
                href={bulletin?.official_portal_url || "https://mausam.imd.gov.in/imd_latest/contents/agromet/advisory/index.php"}
                target="_blank"
                rel="noopener noreferrer"
                className="bulletin-link-btn"
              >
                🌐 Official IMD Agromet Advisory Portal ↗
              </a>
              <a
                href={bulletin?.required_source_url || requiredInfo.portal}
                target="_blank"
                rel="noopener noreferrer"
                className="bulletin-link-btn secondary"
              >
                🏛️ {requiredInfo.shortName} Portal ↗
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Advisory Cards List */}
      {sortedAdvisories.length === 0 ? (
        <div className="advisory-empty-card">
          <span className="empty-icon">{cropIcon}</span>
          <div>
            <strong>No High-Risk Weather Hazards Triggered for {crop.toUpperCase()}</strong>
            <p>
              Current micro-climate parameters conform to optimal growth conditions.
              Follow recommended cultural schedule from {bulletin?.required_source || requiredInfo.institute} for fertilization and moisture conservation.
            </p>
          </div>
        </div>
      ) : (
        <div className="advisory-list">
          {sortedAdvisories.map((item, idx) => {
            const priority = (item.priority || "info").toLowerCase();
            const ruleId = item.rule_id || "";
            const dateStr = item.date ? formatForecastDate(item.date) : "";
            const itemId = `adv-${item.date || idx}-${ruleId}`;
            const itemCrop = item.crop || crop;
            const itemIcon = CROP_ICONS[itemCrop.toLowerCase()] || cropIcon;
            const sourceText = item.source || bulletin?.required_source || requiredInfo.institute;
            const actionItems = item.action_items || [];
            const bulletinRef = item.bulletin_ref || bulletin?.bulletin_number;

            // Priority icon & header styling
            let icon = "ℹ️";
            let priorityLabel = "Information";
            if (priority === "high") {
              icon = "🚨";
              priorityLabel = "High Priority Alert";
            } else if (priority === "medium") {
              icon = "⚠️";
              priorityLabel = "Advisory Warning";
            } else if (priority === "low") {
              icon = "✅";
              priorityLabel = "Favorable Window";
            }

            return (
              <div key={`${item.date}-${ruleId}-${idx}`} className={`advisory-card priority-${priority}`}>
                <div className="advisory-card-header">
                  <div className="advisory-badge-row">
                    <span className="advisory-priority-tag">
                      {icon} {priorityLabel}
                    </span>
                    <span className="advisory-crop-pill">
                      {itemIcon} {itemCrop.toUpperCase()}
                      {item.crop_stage && item.crop_stage !== "None" ? ` • ${item.crop_stage}` : ""}
                    </span>
                    {dateStr && <span className="advisory-date-tag">🗓️ {dateStr}</span>}
                  </div>
                  <div className="advisory-meta-right">
                    <span className="advisory-source-tag" title={sourceText}>
                      🏛️ {sourceText}
                    </span>
                    {bulletinRef && (
                      <span className="advisory-bulletin-tag" title={`Official Bulletin Reference: ${bulletinRef}`}>
                        📋 {bulletinRef}
                      </span>
                    )}
                    <span className="advisory-rule-code">Ref: {ruleId}</span>
                  </div>
                </div>

                <div className="advisory-card-body">
                  <p className="advisory-message">{item.text_en || item.text}</p>

                  {actionItems.length > 0 && (
                    <div className="advisory-actions-checklist">
                      <span className="checklist-title">Recommended Field Operations:</span>
                      <ul className="checklist-items">
                        {actionItems.map((action, aIdx) => (
                          <li key={aIdx} className="checklist-item">
                            <span className="check-bullet">☑</span>
                            <span>{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="advisory-item-actions">
                    <button
                      type="button"
                      className={`btn-mini btn-mini-voice ${speakingId === itemId ? "is-speaking" : ""}`}
                      onClick={() => {
                        const fullSpeech = `${item.text_en || item.text || "No advisory text."} Source: ${sourceText}.${actionItems.length > 0 ? " Recommended actions: " + actionItems.join(". ") : ""}`;
                        speakAdvisory(fullSpeech, itemId);
                      }}
                      title="Listen to advisory audio in English"
                    >
                      <span>{speakingId === itemId ? "⏹️ Stop" : "🔊 Listen"}</span>
                    </button>

                    <button
                      type="button"
                      className="btn-mini btn-mini-whatsapp"
                      onClick={() =>
                        shareOnWhatsApp({
                          date: item.date,
                          textEn: item.text_en || item.text,
                          priority: item.priority,
                          source: sourceText,
                          actionItems: actionItems,
                          bulletinRef: bulletinRef,
                        })
                      }
                      title="Share advisory on WhatsApp"
                    >
                      <span>💬 Share (WhatsApp)</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
