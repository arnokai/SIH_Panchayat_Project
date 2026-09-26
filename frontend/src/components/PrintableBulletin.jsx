export default function PrintableBulletin({ isOpen, onClose, data, crop = "paddy" }) {
  if (!isOpen || !data) return null;

  const handlePrint = () => {
    window.print();
  };

  const todayAdvisory = data.advisories?.[0] || data.forecast?.[0]?.advisory || {};
  const forecastDays = data.forecast || [];

  return (
    <div className="bulletin-modal-backdrop" onClick={onClose}>
      <div className="bulletin-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Print Action Bar */}
        <div className="bulletin-action-bar no-print">
          <div className="bulletin-action-info">
            <span className="bulletin-icon">🖨️</span>
            <div>
              <h3>CSC &amp; Panchayat Bhavan Notice Board Sheet (A4)</h3>
              <p>Optimized for black-and-white or color A4 printing for rural bulletin boards</p>
            </div>
          </div>
          <div className="bulletin-action-buttons">
            <button className="bulletin-print-btn" onClick={handlePrint}>
              🖨️ Print Bulletin (A4)
            </button>
            <button className="bulletin-close-btn" onClick={onClose}>
              ✕ Close
            </button>
          </div>
        </div>

        {/* The Printable A4 Sheet */}
        <div className="bulletin-sheet printable-content">
          {/* Sheet Header */}
          <div className="sheet-header">
            <div className="sheet-logo-block">
              <span className="sheet-emblem">🇮🇳</span>
              <div>
                <h2>TERRAMIND PANCHAYAT WEATHER ADVISORY</h2>
                <h4>MINISTRY OF EARTH SCIENCES (MoES) • SMART INDIA HACKATHON 2026</h4>
              </div>
            </div>
            <div className="sheet-meta-block">
              <div><strong>Panchayat:</strong> {data.panchayat_name} {data.gp_code ? `(LGD: ${data.gp_code})` : ""}</div>
              <div><strong>Block:</strong> {data.block_name || "N/A"}</div>
              <div><strong>District:</strong> {data.district_name || "N/A"}</div>
              <div><strong>Coordinates:</strong> {(data.panchayat_lat ?? data.latitude) != null ? `${(data.panchayat_lat ?? data.latitude).toFixed(4)}°N, ${(data.panchayat_lon ?? data.longitude).toFixed(4)}°E` : "N/A"}</div>
              <div><strong>Elevation:</strong> {data.elevation_m != null ? `${Math.round(data.elevation_m)} m AMSL` : "N/A"}</div>
              <div><strong>Issued:</strong> {new Date().toLocaleDateString("en-IN", { dateStyle: "long" })}</div>
            </div>
          </div>

          <div className="sheet-divider"></div>

          {/* Imperative Action Advisory Alert (English) */}
          <div className="sheet-advisory-section">
            <div className="sheet-advisory-title">
              <span>🌾 TODAY'S MANDATORY CROP ACTION ({crop.toUpperCase()})</span>
              <span className="sheet-priority-badge">{todayAdvisory.priority?.toUpperCase() || "NORMAL"}</span>
            </div>
            <div className="sheet-advisory-columns">
              <div className="sheet-advisory-col full-width">
                <strong>Agricultural Advisory &amp; Field Instruction:</strong>
                <p>{todayAdvisory.text_en || "Normal agricultural field operations recommended."}</p>
              </div>
            </div>
          </div>

          {/* 5-Day Downscaled Forecast Table */}
          <div className="sheet-table-section">
            <h4>FIVE-DAY MICRO-DOWNSCALED FORECAST HORIZON (P10 / P50 / P90)</h4>
            <table className="sheet-forecast-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Rain (P10)</th>
                  <th>Rain Median (P50)</th>
                  <th>Rain Heavy (P90)</th>
                  <th>Tmax (°C)</th>
                  <th>Tmin (°C)</th>
                  <th>Spray Safety Window</th>
                </tr>
              </thead>
              <tbody>
                {forecastDays.map((d) => (
                  <tr key={d.date}>
                    <td><strong>{d.date}</strong></td>
                    <td>{d.rain_mm?.p10 ?? 0} mm</td>
                    <td className="sheet-highlight-rain">{d.rain_mm?.p50 ?? 0} mm</td>
                    <td>{d.rain_mm?.p90 ?? 0} mm</td>
                    <td>{d.tmax_c?.p50 ?? d.tmax_c ?? 32}°C</td>
                    <td>{d.tmin_c ?? 24}°C</td>
                    <td>{d.rain_mm?.p50 >= 10 ? "⚠️ Unsafe: Rain Wash-off" : "✓ Optimal Morning Window"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Weather Risk & Insurance Section */}
          <div className="sheet-insurance-summary">
            <div className="sheet-ins-col">
              <h5>🛡️ PMFBY Weather-Index Status</h5>
              <p>
                24h Excess Rain: <strong>{forecastDays.some((d) => (d.rain_mm?.p50 || 0) >= 60) ? "BREACHED (>60mm)" : "NORMAL"}</strong> | 
                Continuous Dry Spell: <strong>NORMAL</strong>
              </p>
            </div>
            <div className="sheet-ins-col">
              <h5>📞 Free Farmer Support</h5>
              <p>
                Kisan Call Center: <strong>1800-180-1551</strong> | TerraMind IVR: <strong>1800-TERRAMIND</strong>
              </p>
            </div>
          </div>

          {/* Sheet Footer */}
          <div className="sheet-footer">
            <div className="sheet-auth-notice">
              <span>Notice pinned at Gram Panchayat Bhavan &amp; Common Services Centre (CSC). Valid for 24 hours from issuance.</span>
            </div>
            <div className="sheet-signature-block">
              <div className="sheet-sig-line"></div>
              <span>Krishi Sahayak / Panchayat Pradhan Seal</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
