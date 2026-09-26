export default function MultiModelEnsembleCard({ ensembleData, panchayatName = "" }) {
  if (!ensembleData || !ensembleData.models) return null;

  const {
    models = [],
    agreement = "High Consensus",
    confidence_pct = 90,
    spread_mm = 2.4,
    note = "Models strongly align on precipitation magnitude.",
  } = ensembleData;

  let agreementClass = "agreement-high";
  if (confidence_pct < 75) {
    agreementClass = "agreement-low";
  } else if (confidence_pct < 85) {
    agreementClass = "agreement-med";
  }

  return (
    <section className="ensemble-section" aria-label="Multi-Model Weather Ensemble Consensus">
      <div className="ensemble-header">
        <div className="ensemble-title-block">
          <span className="ensemble-icon">🌐</span>
          <div>
            <h3 className="ensemble-title">Multi-Model Ensemble Comparison &amp; Consensus</h3>
            <p className="ensemble-subtitle">
              Benchmarking TerraMind 30m Micro-Terrain Downscaling against ECMWF, GFS, and ICON for {panchayatName || "Active Panchayat"}
            </p>
          </div>
        </div>

        <div className={`ensemble-agreement-badge ${agreementClass}`}>
          <span className="agreement-dot">●</span>
          <span>{agreement} ({confidence_pct}% Confidence)</span>
        </div>
      </div>

      <div className="ensemble-table-wrapper">
        <table className="ensemble-table">
          <thead>
            <tr>
              <th>Numerical Model</th>
              <th>Forecasting Agency</th>
              <th>Spatial Resolution</th>
              <th>Expected Rain (mm)</th>
              <th>Max Temp (°C)</th>
              <th>Verification Tier</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => {
              const isHighlight = m.highlight;
              return (
                <tr key={m.model_id} className={isHighlight ? "highlighted-model-row" : ""}>
                  <td className="model-name-cell">
                    <strong>{m.name}</strong>
                    {isHighlight && <span className="local-model-chip">Active System</span>}
                  </td>
                  <td>{m.agency}</td>
                  <td>
                    <span className="resolution-tag">{m.resolution}</span>
                  </td>
                  <td className="rain-cell">
                    <strong>{m.rain_mm.toFixed(1)} mm</strong>
                  </td>
                  <td>{m.tmax_c.toFixed(1)}°C</td>
                  <td>
                    <span className={`model-tier-chip ${isHighlight ? "tier-primary" : "tier-coarse"}`}>
                      {m.badge}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="ensemble-footer-note">
        <span className="note-icon">💡</span>
        <span>
          <strong>Ensemble Synthesis:</strong> {note} Inter-model precipitation spread is <strong>{spread_mm} mm</strong>.
        </span>
      </div>
    </section>
  );
}
