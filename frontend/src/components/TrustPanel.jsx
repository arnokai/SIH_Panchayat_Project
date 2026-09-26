import { useState, useEffect } from "react";
import { fetchYesterdayTrust } from "../services/api";

export default function TrustPanel({ panchayatId, lang = "en" }) {
  const [trustData, setTrustData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    if (!panchayatId) return;

    setLoading(true);
    setError(false);

    fetchYesterdayTrust(panchayatId)
      .then((data) => {
        if (active) {
          setTrustData(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          console.warn("Could not load yesterday trust metrics:", err);
          setError(true);
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [panchayatId]);

  if (loading) {
    return (
      <div className="trust-panel-loading">
        <span className="trust-spinner"></span>
        <span>Verifying yesterday's model calibration against ground-truth station observations...</span>
      </div>
    );
  }

  if (error || !trustData) {
    return null;
  }

  const badgeText = trustData.badge_text || "Calibrated";

  return (
    <div className="trust-panel-card">
      <div className="trust-panel-header">
        <div className="trust-title-group">
          <span className="trust-icon">⚖️</span>
          <div>
            <h3>
              Yesterday We Said vs. Actual Happened
            </h3>
            <p className="trust-subtitle">
              Evaluated Date: {trustData.evaluation_date} • Ground-truth cross-referenced with AWS telemetry
            </p>
          </div>
        </div>
        <div className="trust-badge-pill">
          <span className="trust-check-icon">✓</span>
          <span className="trust-badge-label">{badgeText}</span>
        </div>
      </div>

      <div className="trust-grid">
        <div className="trust-metric-box">
          <span className="trust-metric-title">
            Yesterday Predicted (P50)
          </span>
          <div className="trust-metric-val">
            <span className="trust-val-num">{trustData.predicted_rain_p50}</span>
            <span className="trust-val-unit">mm</span>
          </div>
          <span className="trust-spread-hint">
            P10: {trustData.predicted_rain_p10}mm — P90: {trustData.predicted_rain_p90}mm
          </span>
        </div>

        <div className="trust-vs-divider">
          <span>VS</span>
        </div>

        <div className="trust-metric-box actual-box">
          <span className="trust-metric-title">
            Actual Rain Recorded
          </span>
          <div className="trust-metric-val">
            <span className="trust-val-num">{trustData.actual_rain_recorded}</span>
            <span className="trust-val-unit">mm</span>
          </div>
          <span className="trust-spread-hint error-hint">
            Margin: ±{trustData.error_margin_mm} mm
          </span>
        </div>

        <div className="trust-calibration-box">
          <div className="trust-calib-header">
            <span>30-Day Model Reliability</span>
            <strong>{trustData.calibration_score_pct}%</strong>
          </div>
          <div className="trust-calib-bar-track">
            <div
              className="trust-calib-bar-fill"
              style={{ width: `${trustData.calibration_score_pct}%` }}
            ></div>
          </div>
          <span className="trust-source-footnote">
            {trustData.observation_source}
          </span>
        </div>
      </div>
    </div>
  );
}
