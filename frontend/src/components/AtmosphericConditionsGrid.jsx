import { useState } from "react";

export default function AtmosphericConditionsGrid({ liveWeather, airQuality }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const current = liveWeather?.current || {};
  const aq = airQuality || liveWeather?.air_quality || {};

  const temp = current.temperature_2m ?? 30.0;
  const feelsLike = current.apparent_temperature ?? temp;
  const dewPoint = current.dew_point_c ?? 22.0;
  const humidity = current.relative_humidity_2m ?? 78;
  const uvVal = current.uv_index ?? 6.5;
  const uvRating = current.uv_rating || "Moderate";
  const visibility = current.visibility_km ?? 10.0;
  const cloudCover = current.cloud_cover_pct ?? 45;
  const pressure = current.surface_pressure_hpa ?? 1010.0;
  const pressureTendency = current.pressure_tendency || "Steady";
  const windKmh = current.wind_speed_10m ?? 12.0;
  const windCompass = current.wind_compass || "S";
  const windDeg = current.wind_direction_deg ?? 180;

  // Dew point fungal risk badge
  let dewRisk = "Low Fungal Risk";
  let dewRiskClass = "dew-risk-low";
  if (dewPoint >= 24.0) {
    dewRisk = "High Condensation / Blast Risk";
    dewRiskClass = "dew-risk-high";
  } else if (dewPoint >= 20.0) {
    dewRisk = "Moderate Moisture Risk";
    dewRiskClass = "dew-risk-med";
  }

  // UV badge color
  let uvColor = "#10b981";
  if (uvVal >= 8.0) uvColor = "#dc2626";
  else if (uvVal >= 6.0) uvColor = "#ea580c";
  else if (uvVal >= 3.0) uvColor = "#f59e0b";

  // AQI color
  const aqiScore = aq.aqi ?? 45;
  const aqiCat = aq.category || "Good";
  const aqiColor = aq.color || "#10b981";

  return (
    <section className="weather-metrics-card" aria-label="Atmospheric Conditions Grid">
      <div className="metrics-card-header">
        <div className="metrics-header-title">
          <span className="metrics-header-icon">🧭</span>
          <div>
            <h3 className="metrics-title">Atmospheric Conditions &amp; Environmental Quality</h3>
            <p className="metrics-subtitle">
              Comprehensive physical parameters, moisture saturation, and occupational safety telemetry
            </p>
          </div>
        </div>

        <button
          type="button"
          className="metrics-expand-toggle"
          onClick={() => setIsExpanded((prev) => !prev)}
        >
          {isExpanded ? "Collapse Details 🗕" : "View All Metrics 🗖"}
        </button>
      </div>

      <div className="metrics-grid">
        {/* 1. RealFeel Heat Index */}
        <div className="metric-tile">
          <div className="metric-tile-top">
            <span className="metric-label">RealFeel® / Feels Like</span>
            <span className="metric-icon">🌡️</span>
          </div>
          <div className="metric-val-row">
            <span className="metric-primary-val">{feelsLike.toFixed(1)}°</span>
            <span className="metric-unit">C</span>
          </div>
          <div className="metric-subtext">
            {feelsLike > temp
              ? `+${(feelsLike - temp).toFixed(1)}°C heat index from ${humidity}% humidity`
              : feelsLike < temp
              ? `${(feelsLike - temp).toFixed(1)}°C wind chill from ${windKmh} km/h wind`
              : "Matches actual dry-bulb air temperature"}
          </div>
        </div>

        {/* 2. Dew Point */}
        <div className="metric-tile">
          <div className="metric-tile-top">
            <span className="metric-label">Dew Point Condensation</span>
            <span className="metric-icon">💧</span>
          </div>
          <div className="metric-val-row">
            <span className="metric-primary-val">{dewPoint.toFixed(1)}°</span>
            <span className="metric-unit">C</span>
          </div>
          <div className={`metric-badge ${dewRiskClass}`}>
            <span>{dewRisk}</span>
          </div>
        </div>

        {/* 3. Solar UV Index */}
        <div className="metric-tile">
          <div className="metric-tile-top">
            <span className="metric-label">Solar UV Index</span>
            <span className="metric-icon">☀️</span>
          </div>
          <div className="metric-val-row">
            <span className="metric-primary-val" style={{ color: uvColor }}>
              {uvVal.toFixed(1)}
            </span>
            <span className="metric-rating-tag" style={{ backgroundColor: uvColor }}>
              {uvRating}
            </span>
          </div>
          <div className="metric-subtext">
            {uvVal >= 8
              ? "Seek shade 11:30 AM – 2:30 PM. Wear head covering."
              : uvVal >= 5
              ? "Moderate sun intensity. Straw hat advised."
              : "Low sun hazard. Safe for full-day field work."}
          </div>
        </div>

        {/* 4. Air Quality Index (AQI) */}
        <div className="metric-tile">
          <div className="metric-tile-top">
            <span className="metric-label">Air Quality (AQI)</span>
            <span className="metric-icon">🍃</span>
          </div>
          <div className="metric-val-row">
            <span className="metric-primary-val" style={{ color: aqiColor }}>
              {aqiScore}
            </span>
            <span className="metric-rating-tag" style={{ backgroundColor: aqiColor }}>
              {aqiCat}
            </span>
          </div>
          <div className="metric-subtext">
            PM2.5: <strong>{aq.pm25 ?? 15} µg/m³</strong> • PM10: <strong>{aq.pm10 ?? 30} µg/m³</strong>
          </div>
        </div>

        {/* Expanded Grid Tiles */}
        {isExpanded && (
          <>
            {/* 5. Cloud Cover */}
            <div className="metric-tile">
              <div className="metric-tile-top">
                <span className="metric-label">Cloud Cover</span>
                <span className="metric-icon">☁️</span>
              </div>
              <div className="metric-val-row">
                <span className="metric-primary-val">{Math.round(cloudCover)}</span>
                <span className="metric-unit">%</span>
              </div>
              <div className="metric-subtext">
                {cloudCover >= 75
                  ? "Overcast skies with restricted photosynthesis"
                  : cloudCover >= 40
                  ? "Partly cloudy with intermittent sunshine"
                  : "Clear blue skies with high solar radiation"}
              </div>
            </div>

            {/* 6. Visibility */}
            <div className="metric-tile">
              <div className="metric-tile-top">
                <span className="metric-label">Atmospheric Visibility</span>
                <span className="metric-icon">👁️</span>
              </div>
              <div className="metric-val-row">
                <span className="metric-primary-val">{visibility.toFixed(1)}</span>
                <span className="metric-unit">km</span>
              </div>
              <div className="metric-subtext">
                {visibility >= 10
                  ? "Excellent atmospheric clarity (no fog/mist)"
                  : visibility >= 5
                  ? "Moderate haze / light precipitation obscurity"
                  : "Low visibility due to heavy rain or mist"}
              </div>
            </div>

            {/* 7. Barometric Pressure */}
            <div className="metric-tile">
              <div className="metric-tile-top">
                <span className="metric-label">Surface Pressure</span>
                <span className="metric-icon">⏲️</span>
              </div>
              <div className="metric-val-row">
                <span className="metric-primary-val">{pressure.toFixed(1)}</span>
                <span className="metric-unit">hPa</span>
              </div>
              <div className="metric-subtext">
                Tendency: <strong>{pressureTendency}</strong>
              </div>
            </div>

            {/* 8. Wind Direction & Compass */}
            <div className="metric-tile">
              <div className="metric-tile-top">
                <span className="metric-label">Wind Direction</span>
                <span className="metric-icon">🧭</span>
              </div>
              <div className="metric-val-row">
                <span className="metric-primary-val">{windCompass}</span>
                <span className="metric-unit">({Math.round(windDeg)}°)</span>
              </div>
              <div className="metric-subtext">
                Velocity: <strong>{windKmh.toFixed(1)} km/h</strong> • Maritime inflow
              </div>
            </div>
          </>
        )}
      </div>

      {/* Occupational Health Notice */}
      <div className="metrics-health-banner">
        <span className="health-icon">🌾</span>
        <span className="health-text">
          <strong>Field Health Guidance:</strong> {aq.health_recommendation || "Normal outdoor field conditions. Maintain hydration during afternoon weeding."}
        </span>
      </div>
    </section>
  );
}
