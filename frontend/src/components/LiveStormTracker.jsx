import { useState, useEffect, useCallback } from "react";
import { fetchCycloneTracker } from "../services/api";

export default function LiveStormTracker({ activePanchayat, panchayatId }) {
  const [cycloneData, setCycloneData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const loadCycloneData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const lat = activePanchayat?.latitude;
      const lon = activePanchayat?.longitude;
      const data = await fetchCycloneTracker(panchayatId, lat, lon);
      setCycloneData(data);
    } catch (err) {
      console.warn("Could not fetch cyclone data:", err);
      setError("Unable to update live cyclone data from server.");
    } finally {
      setLoading(false);
    }
  }, [panchayatId, activePanchayat?.latitude, activePanchayat?.longitude]);

  useEffect(() => {
    loadCycloneData();
    const interval = setInterval(loadCycloneData, 300000); // 5 minutes
    return () => clearInterval(interval);
  }, [loadCycloneData]);

  if (!cycloneData || !cycloneData.has_active_system) {
    return null;
  }

  const { storm } = cycloneData;
  const relative = storm.relative_to_gp || {};
  const panchayatName = activePanchayat?.panchayat_name || "Active Panchayat";

  return (
    <section className="cyclone-tracker-card" aria-label="Severe Storm & Cyclone Tracker">
      {/* Header Banner */}
      <div className="cyclone-header">
        <div className="cyclone-title-block">
          <div className="cyclone-pulse-indicator">
            <span className="cyclone-beacon-ring"></span>
            <span className="cyclone-beacon-dot"></span>
          </div>
          <div>
            <div className="cyclone-eyebrow-row">
              <span className="cyclone-tag">IMD RSMC CYCLONE &amp; STORM RADAR</span>
              <span className="cyclone-classification-badge">{storm.classification.toUpperCase()}</span>
              <span className="cyclone-threat-chip" style={{ backgroundColor: relative.threat_color }}>
                {relative.threat_level} PROXIMITY
              </span>
            </div>
            <h3 className="cyclone-main-title">{storm.name}</h3>
          </div>
        </div>

        <div className="cyclone-header-actions">
          <button
            type="button"
            className="cyclone-refresh-btn"
            onClick={loadCycloneData}
            disabled={loading}
            title="Refresh live cyclone tracking telemetry"
          >
            {loading ? "⏳ Syncing..." : "🔄 Refresh IMD Bulletin"}
          </button>
          <button
            type="button"
            className="cyclone-collapse-btn"
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? "Expand storm tracker" : "Minimize storm tracker"}
          >
            {isCollapsed ? "▼ Show Details" : "▲ Minimize"}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="cyclone-body">
          {/* Key Storm Metric Grid */}
          <div className="cyclone-metrics-grid">
            {/* Distance to Selected GP */}
            <div className="cyclone-metric-cell highlight-cell">
              <span className="metric-label">DISTANCE FROM {panchayatName.toUpperCase()} GP</span>
              <strong className="metric-value">{relative.distance_km} km</strong>
              <small className="metric-sub">Bearing: {relative.bearing} ({relative.direction_phrase})</small>
            </div>

            {/* Current Position */}
            <div className="cyclone-metric-cell">
              <span className="metric-label">CURRENT CENTER LOCATION</span>
              <strong className="metric-value">
                {storm.current_coordinates.latitude}°N, {storm.current_coordinates.longitude}°E
              </strong>
              <small className="metric-sub">{storm.current_coordinates.location_description}</small>
            </div>

            {/* Wind & Pressure */}
            <div className="cyclone-metric-cell">
              <span className="metric-label">INTENSITY &amp; CENTRAL PRESSURE</span>
              <strong className="metric-value">{storm.intensity.sustained_wind_kmh}–{storm.intensity.gusts_kmh} km/h</strong>
              <small className="metric-sub">Pressure: {storm.intensity.central_pressure_hpa} hPa • Moving {storm.trajectory.direction}</small>
            </div>

            {/* Port Signals */}
            <div className="cyclone-metric-cell">
              <span className="metric-label">PORT CAUTIONARY SIGNALS</span>
              <strong className="metric-value port-warning-text">LC3 Hoisted</strong>
              <small className="metric-sub">Kolkata Port &amp; Haldia Port</small>
            </div>
          </div>

          {/* Warnings & Advisories Row */}
          <div className="cyclone-advisories-row">
            {/* Marine & Fishermen Warning */}
            <div className="advisory-pill marine-pill">
              <span className="advisory-icon">🌊</span>
              <div>
                <strong>Coastal &amp; Marine Alert:</strong> {storm.marine_warnings.fishermen_alert}
              </div>
            </div>

            {/* Regional Rainfall Impact */}
            <div className="advisory-pill rain-pill">
              <span className="advisory-icon">🌧️</span>
              <div>
                <strong>West Bengal Moisture Band:</strong> {storm.regional_rain_threat.phenomenon}
                <span className="risk-districts-list">
                  {" "}Target Districts: {storm.regional_rain_threat.high_risk_districts.join(", ")}.
                </span>
              </div>
            </div>
          </div>

          {/* Landfall & Historical Trajectory Summary */}
          <div className="cyclone-landfall-strip">
            <span>📍 <strong>Landfall Verified:</strong> {storm.landfall.location} on {storm.landfall.time}.</span>
            <span>💨 <strong>Trajectory:</strong> {storm.trajectory.projected_fate}.</span>
          </div>

          {/* Educational Accordion: Why wasn't it named Cyclone Arnab? */}
          <div className="cyclone-explainer-section">
            <button
              type="button"
              className="explainer-toggle-btn"
              onClick={() => setShowExplanation(!showExplanation)}
            >
              <span>ℹ️ Why was this system not named <strong>Cyclonic Storm "Arnab"</strong>?</span>
              <span>{showExplanation ? "− Hide" : "+ Read Scientific Explanation"}</span>
            </button>

            {showExplanation && (
              <div className="explainer-content">
                <p>
                  Under the World Meteorological Organization (WMO) / ESCAP Panel on Tropical Cyclones guidelines,
                  a low-pressure disturbance in the North Indian Ocean / Bay of Bengal is only officially assigned
                  a regional name when its maximum sustained surface wind speeds reach <strong>62 km/h (34 knots)</strong> or higher.
                </p>
                <p>
                  While public anticipation associated this system with the name <strong>"Arnab"</strong> (the next reserved
                  name contributed by Bangladesh), IMD radar and satellite scatterometer observations confirmed peak winds of
                  <strong> 55 km/h</strong>, classifying it strictly as a <strong>Deep Depression</strong>.
                  Consequently, the name <em>Arnab</em> remains safely stored on the naming roster for the next tropical storm.
                </p>
                <small className="explainer-source">
                  Ground Truth Source: {storm.bulletin_source} • Synchronized with TerraMind Real-Time Telemetry.
                </small>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
