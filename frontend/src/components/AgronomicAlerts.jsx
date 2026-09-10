import { formatForecastDate } from "../utils/formatters";

export default function AgronomicAlerts({ advisories = [], crop = "paddy" }) {
  if (!advisories || advisories.length === 0) {
    return (
      <section className="advisory-section">
        <div className="section-header">
          <div>
            <h3 className="section-title">Field Agricultural Advisories</h3>
            <p className="section-subtitle">
              Heuristic agronomic guidance based on 5-day downscaled parameters for {crop}
            </p>
          </div>
        </div>
        <div className="advisory-empty-card">
          <span className="empty-icon">🌱</span>
          <div>
            <strong>No High-Risk Weather Hazards Triggered</strong>
            <p>
              Weather conditions are favorable. Follow standard schedule for irrigation, fertilization, and weeding.
            </p>
          </div>
        </div>
      </section>
    );
  }

  // Sort advisories: High priority first, then medium, then low
  const priorityOrder = { high: 0, medium: 1, low: 2, info: 3 };
  const sortedAdvisories = [...advisories].sort((a, b) => {
    const pA = priorityOrder[a.priority?.toLowerCase()] ?? 99;
    const pB = priorityOrder[b.priority?.toLowerCase()] ?? 99;
    return pA - pB;
  });

  return (
    <section className="advisory-section">
      <div className="section-header">
        <div>
          <h3 className="section-title">Field Agricultural Advisories & Alerts</h3>
          <p className="section-subtitle">
            Actionable farming recommendations for <strong>{crop.toUpperCase()}</strong> based on 5-day weather
          </p>
        </div>
        <div className="advisory-count-badge">
          {sortedAdvisories.length} Active {sortedAdvisories.length === 1 ? "Advisory" : "Advisories"}
        </div>
      </div>

      <div className="advisory-list">
        {sortedAdvisories.map((item, idx) => {
          const priority = (item.priority || "info").toLowerCase();
          const ruleId = item.rule_id || "";
          const dateStr = item.date ? formatForecastDate(item.date) : "";

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
                  {dateStr && <span className="advisory-date-tag">🗓️ {dateStr}</span>}
                </div>
                <span className="advisory-rule-code">Advisory Ref: {ruleId}</span>
              </div>

              <div className="advisory-card-body">
                <p className="advisory-message">{item.text || item.text_en}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
