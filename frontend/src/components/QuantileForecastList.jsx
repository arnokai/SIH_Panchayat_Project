import { formatForecastDate, getActionChip } from "../utils/formatters";

export default function QuantileForecastList({ forecast = [], onSelectDate, selectedDate }) {
  if (!forecast || forecast.length === 0) return null;

  const getRainCategoryTag = (rainMm) => {
    if (rainMm == null || rainMm <= 0.1) return "Dry & Clear";
    if (rainMm < 2.5) return "Light Rain";
    if (rainMm < 15.0) return "Moderate Rain";
    if (rainMm < 35.0) return "Heavy Rain";
    return "Very Heavy Rain";
  };

  return (
    <section className="forecast-section">
      <div className="section-header">
        <div>
          <h3 className="section-title">5-Day Weather & Farming Horizon</h3>
          <p className="section-subtitle">
            Daily rainfall forecast, confidence range (Min to Max), and recommended field actions
          </p>
        </div>
      </div>

      <div className="forecast-grid">
        {forecast.map((day, idx) => {
          const dateFormatted = formatForecastDate(day.date);
          const p10 = day.rain_mm?.p10 ?? (typeof day.rain_mm === "number" ? day.rain_mm : 0);
          const p50 = day.rain_mm?.p50 ?? (typeof day.rain_mm === "number" ? day.rain_mm : 0);
          const p90 = day.rain_mm?.p90 ?? (typeof day.rain_mm === "number" ? day.rain_mm : 0);
          const tmax = day.tmax_c?.p50 ?? day.tmax_c ?? "--";
          const tmin = day.tmin_c ?? "--";
          const rainProb = Math.round((day.rain_probability ?? 0) * 100);

          const chip = getActionChip(day.advisory?.rule_id, p50);
          const isSelected = selectedDate === day.date;
          const categoryTag = getRainCategoryTag(p50);

          // Max scaling for quantile bar (capped at 50mm for UI balance)
          const barMax = Math.max(25, Math.min(60, p90 * 1.25));
          const p10Pct = Math.min(100, Math.max(0, (p10 / barMax) * 100));
          const p50Pct = Math.min(100, Math.max(0, (p50 / barMax) * 100));
          const p90Pct = Math.min(100, Math.max(0, (p90 / barMax) * 100));

          return (
            <div
              key={day.date || idx}
              className={`forecast-card ${isSelected ? "selected" : ""}`}
              onClick={() => onSelectDate && onSelectDate(day.date)}
            >
              {/* Day & Date Header */}
              <div className="card-header">
                <div className="card-date-badge">
                  {idx === 0 ? "Today" : idx === 1 ? "Tomorrow" : `Day +${idx}`}
                </div>
                <div className="card-date">{dateFormatted}</div>
              </div>

              {/* Temperature & Rain Probability */}
              <div className="card-temp-prob-row">
                <div className="card-temp">
                  <span className="tmax">{Math.round(tmax)}°</span>
                  <span className="temp-sep">/</span>
                  <span className="tmin">{Math.round(tmin)}°C</span>
                </div>
                <div className="card-rain-prob" title="Probability of precipitation">
                  <span>🌧️ {rainProb}%</span>
                </div>
              </div>

              {/* Quantile Uncertainty Bar */}
              <div className="uncertainty-box">
                <div className="uncertainty-header">
                  <div>
                    <span className="rain-title">Expected Rain</span>
                    <span className="rain-category-pill">{categoryTag}</span>
                  </div>
                  <span className="rain-median">{p50.toFixed(1)} mm</span>
                </div>

                <div className="quantile-bar-track">
                  {/* Uncertainty range band from P10 to P90 */}
                  <div
                    className="quantile-spread-fill"
                    style={{
                      left: `${p10Pct}%`,
                      width: `${Math.max(4, p90Pct - p10Pct)}%`,
                    }}
                    title={`P10–P90 Range: ${p10.toFixed(1)}mm to ${p90.toFixed(1)}mm`}
                  />
                  {/* P50 Median marker */}
                  <div
                    className="quantile-median-marker"
                    style={{ left: `${p50Pct}%` }}
                    title={`P50 Median: ${p50.toFixed(1)}mm`}
                  />
                </div>

                <div className="quantile-labels">
                  <span title={`Statistical Lower Bound P10: ${p10.toFixed(1)} mm`}>Min: {p10.toFixed(1)} mm</span>
                  <span title={`Statistical Upper Bound P90: ${p90.toFixed(1)} mm`}>Max: {p90.toFixed(1)} mm</span>
                </div>
              </div>

              {/* Action Badge */}
              <div className={`action-chip ${chip.type}`}>
                <span className="action-icon">{chip.icon}</span>
                <div className="action-text">
                  <strong>{chip.label}</strong>
                  <span className="action-desc">{chip.desc}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
