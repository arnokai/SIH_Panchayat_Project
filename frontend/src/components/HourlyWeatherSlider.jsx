import { useState } from "react";

/**
 * Returns weather icon URL based on WMO weather code and daylight status.
 */
function getWeatherIcon(code, isDaylight = true) {
  if (code == null) {
    return isDaylight
      ? "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy.png"
      : "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy_night.png";
  }
  if (code === 0) {
    return isDaylight
      ? "https://ssl.gstatic.com/onebox/weather/64/sunny.png"
      : "https://ssl.gstatic.com/onebox/weather/64/night.png";
  }
  if (code >= 1 && code <= 3) {
    return isDaylight
      ? "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy.png"
      : "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy_night.png";
  }
  if (code === 45 || code === 48) {
    return "https://ssl.gstatic.com/onebox/weather/64/cloudy.png";
  }
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) {
    return "https://ssl.gstatic.com/onebox/weather/64/rain.png";
  }
  if ((code >= 71 && code <= 77) || (code >= 85 && code <= 86)) {
    return "https://ssl.gstatic.com/onebox/weather/64/snow.png";
  }
  if (code >= 95) {
    return "https://ssl.gstatic.com/onebox/weather/64/thunderstorms.png";
  }
  return isDaylight
    ? "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy.png"
    : "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy_night.png";
}

/**
 * Maps spray safety code to badge styling and label.
 */
function getSprayBadgeInfo(safety) {
  switch (safety) {
    case "optimal":
      return {
        badgeClass: "spray-badge-optimal",
        shortLabel: "Safe",
        icon: "✓",
      };
    case "caution":
      return {
        badgeClass: "spray-badge-caution",
        shortLabel: "Caution",
        icon: "⚠",
      };
    case "unsafe_rain":
      return {
        badgeClass: "spray-badge-unsafe",
        shortLabel: "Rain Risk",
        icon: "✕",
      };
    case "unsafe_wind":
      return {
        badgeClass: "spray-badge-unsafe",
        shortLabel: "High Wind",
        icon: "✕",
      };
    default:
      return {
        badgeClass: "spray-badge-neutral",
        shortLabel: "Normal",
        icon: "•",
      };
  }
}

/**
 * Returns effective 24-hour records with guaranteed non-null fallback.
 */
function getEffectiveRecords(data) {
  const liveRecords = data?.live_weather?.hourly?.records;
  if (Array.isArray(liveRecords) && liveRecords.length > 0) {
    return liveRecords.slice(0, 24);
  }

  // Fallback 1: Parallel arrays present without records list
  const hourly = data?.live_weather?.hourly;
  if (hourly?.time && Array.isArray(hourly.time) && hourly.time.length > 0) {
    return hourly.time.slice(0, 24).map((tStr, idx) => {
      const dtHour = parseInt(tStr.split("T")[1]?.split(":")[0] || "12", 10);
      const displayTime = `${dtHour % 12 || 12} ${dtHour < 12 ? "AM" : "PM"}`;
      const tempVal = hourly.temperature_2m?.[idx] ?? 28;
      const probVal = hourly.precipitation_probability?.[idx] ?? 0;
      const rainVal = hourly.precipitation?.[idx] ?? 0;
      const windVal = hourly.wind_speed_10m?.[idx] ?? 5;
      const codeVal = hourly.weather_code?.[idx] ?? 1;

      let safety = "optimal";
      let label = "Optimal: Safe for Spraying";
      if (rainVal >= 0.2 || probVal >= 50) {
        safety = "unsafe_rain";
        label = "Unsafe: Rain Wash-off Risk";
      } else if (windVal >= 15) {
        safety = "unsafe_wind";
        label = "Unsafe: Chemical Drift Hazard";
      } else if (windVal >= 10 || probVal >= 30) {
        safety = "caution";
        label = "Caution: Moderate Wind / Drizzle Risk";
      }

      return {
        time: tStr,
        hour: tStr.split("T")[1]?.slice(0, 5) || "12:00",
        display_time: displayTime,
        temperature_c: tempVal,
        precipitation_probability: probVal,
        precipitation_mm: rainVal,
        wind_speed_kmh: windVal,
        weather_code: codeVal,
        spray_safety: safety,
        spray_safety_label: label,
        is_daylight: dtHour >= 6 && dtHour <= 18,
      };
    });
  }

  // Fallback 2: Synthesize diurnal curve from Day 1 forecast
  const day0 = data?.forecast?.[0];
  const tmax = day0?.tmax_c?.p50 ?? 32;
  const tmin = day0?.tmin_c ?? 24;
  const probVal = Math.round((day0?.rain_probability ?? 0) * 100);
  const rainMm = day0?.rain_mm?.p50 ?? 0;

  const records = [];
  for (let h = 0; h < 24; h++) {
    const displayTime = `${h % 12 || 12} ${h < 12 ? "AM" : "PM"}`;
    const diurnalFactor =
      h >= 5 && h <= 14
        ? 0.5 * (1.0 - Math.cos((Math.PI * (h - 5)) / 9.0))
        : 0.5 * (1.0 + Math.cos((Math.PI * ((h - 14 + 24) % 24)) / 15.0));

    const tempH = Math.round((tmin + (tmax - tmin) * diurnalFactor) * 10) / 10;
    const windH = Math.round((4.0 + 7.0 * (1.0 - Math.abs(h - 14) / 14.0)) * 10) / 10;
    const isDaylight = h >= 6 && h <= 18;

    let safety = "optimal";
    let label = "Optimal: Safe for Spraying";
    if (rainMm >= 0.2 || probVal >= 50) {
      safety = "unsafe_rain";
      label = "Unsafe: Rain Wash-off Risk";
    } else if (windH >= 15) {
      safety = "unsafe_wind";
      label = "Unsafe: Chemical Drift Hazard";
    } else if (windH >= 10 || probVal >= 30) {
      safety = "caution";
      label = "Caution: Moderate Wind / Drizzle Risk";
    }

    records.push({
      time: `T${String(h).padStart(2, "0")}:00`,
      hour: `${String(h).padStart(2, "0")}:00`,
      display_time: displayTime,
      temperature_c: tempH,
      precipitation_probability: probVal,
      precipitation_mm: rainMm > 0 && h >= 13 && h <= 17 ? Math.round((rainMm / 3) * 10) / 10 : 0,
      wind_speed_kmh: windH,
      weather_code: rainMm > 0 ? 61 : 1,
      spray_safety: safety,
      spray_safety_label: label,
      is_daylight: isDaylight,
    });
  }

  return records;
}

export default function HourlyWeatherSlider({ data, onToggleLive }) {
  const [activeTab, setActiveTab] = useState("temperature");

  const records = getEffectiveRecords(data);
  const liveWeather = data?.live_weather;
  const isDynamic = data?.is_live_dynamic ?? false;
  const operationalInsight =
    liveWeather?.operational_insight ||
    "Safe spraying conditions anticipated in early morning daylight hours (07:00 – 10:00). Check local wind drift before application.";
  const refinement = liveWeather?.operational_refinement;

  return (
    <section className="hourly-slider-card">
      {/* Top Header & Tab Controls */}
      <div className="hourly-header">
        <div className="hourly-title-group">
          <div className="hourly-title-row">
            <span className="hourly-badge-icon">⚡</span>
            <h3 className="hourly-title">HOURLY WEATHER & SPRAY WINDOW</h3>
            <span className={`hourly-mode-badge ${isDynamic ? "live" : "offline"}`}>
              {isDynamic ? "🟢 LIVE STREAM" : "🟡 BASELINE FORECAST"}
            </span>
          </div>
          <p className="hourly-subtitle">
            24-hour hour-by-hour forecast and farmer spraying recommendations
          </p>
        </div>

        {/* Tab Switcher & Mode Actions */}
        <div className="hourly-controls-group">
          {!isDynamic && onToggleLive && (
            <button
              type="button"
              className="hourly-activate-live-btn"
              onClick={onToggleLive}
              title="Connect to Open-Meteo live ECMWF/GFS stream"
            >
              ⚡ Switch to Live Dynamic
            </button>
          )}

          <div className="hourly-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "temperature"}
              className={`hourly-tab-btn ${activeTab === "temperature" ? "active" : ""}`}
              onClick={() => setActiveTab("temperature")}
            >
              🌡️ Temperature
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "precipitation"}
              className={`hourly-tab-btn ${activeTab === "precipitation" ? "active" : ""}`}
              onClick={() => setActiveTab("precipitation")}
            >
              🌧️ Rain Chance
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "spray"}
              className={`hourly-tab-btn ${activeTab === "spray" ? "active" : ""}`}
              onClick={() => setActiveTab("spray")}
            >
              🚜 Spraying Safety
            </button>
          </div>
        </div>
      </div>

      {/* Horizontal Scrollable Slider */}
      <div className="hourly-scroll-container">
        <div className="hourly-track">
          {records.map((rec, idx) => {
            const isFirst = idx === 0;
            const timeLabel = isFirst ? "Now" : rec.display_time;
            const iconUrl = getWeatherIcon(rec.weather_code, rec.is_daylight);
            const badge = getSprayBadgeInfo(rec.spray_safety);

            return (
              <div
                key={rec.time || idx}
                className={`hourly-cell ${isFirst ? "current-hour" : ""} ${
                  rec.is_daylight ? "daylight" : "nighttime"
                }`}
              >
                {/* Time */}
                <div className="hourly-cell-time">{timeLabel}</div>

                {/* Weather Icon */}
                <div className="hourly-cell-icon-wrap">
                  <img
                    src={iconUrl}
                    alt="Weather condition"
                    className="hourly-cell-icon"
                    loading="lazy"
                  />
                </div>

                {/* Tab Specific Metric */}
                {activeTab === "temperature" && (
                  <div className="hourly-metric-block">
                    <div className="hourly-temp-value">
                      {rec.temperature_c != null ? `${Math.round(rec.temperature_c)}°` : "--"}
                    </div>
                    {rec.precipitation_probability >= 20 ? (
                      <div className="hourly-sub-metric rain-prob">
                        💧 {Math.round(rec.precipitation_probability)}%
                      </div>
                    ) : (
                      <div className="hourly-sub-metric calm">Dry</div>
                    )}
                  </div>
                )}

                {activeTab === "precipitation" && (
                  <div className="hourly-metric-block">
                    <div className="hourly-rain-prob-value">
                      {Math.round(rec.precipitation_probability)}%
                    </div>
                    <div className="hourly-rain-bar-wrap">
                      <div
                        className="hourly-rain-bar-fill"
                        style={{ width: `${Math.min(100, Math.max(8, rec.precipitation_probability))}%` }}
                      ></div>
                    </div>
                    <div className="hourly-sub-metric">
                      {rec.precipitation_mm > 0 ? `${rec.precipitation_mm.toFixed(1)} mm` : "0.0 mm"}
                    </div>
                  </div>
                )}

                {activeTab === "spray" && (
                  <div className="hourly-metric-block">
                    <div className="hourly-wind-value">
                      {Math.round(rec.wind_speed_kmh)} <span className="unit">km/h</span>
                    </div>
                    <div
                      className={`spray-pill ${badge.badgeClass}`}
                      title={rec.spray_safety_label}
                    >
                      <span className="spray-pill-icon">{badge.icon}</span>
                      <span>{badge.shortLabel}</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Operational Spray Advisory & Refinement Banner */}
      <div className="hourly-advisory-banner">
        <div className="hourly-advisory-left">
          <span className="advisory-icon">🚜</span>
          <div>
            <div className="advisory-heading">
              <strong>🚜 TODAY'S FARM WORK ADVICE</strong>
              {refinement?.status === "applied" && (
                <span className="dem-lapse-pill">
                  Terrain: {Math.round(refinement.relative_elevation_m)}m elevation ({refinement.lapse_rate_c > 0 ? "+" : ""}
                  {refinement.lapse_rate_c}°C adj.)
                </span>
              )}
            </div>
            <p className="advisory-text">{operationalInsight}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
