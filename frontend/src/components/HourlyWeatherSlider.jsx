import { useState } from "react";
import WeatherIcon from "./WeatherIcon";
import { formatForecastDate } from "../utils/formatters";

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
 * Dynamically synthesizes the operational spray window from 24-hour records.
 */
function computeOperationalInsight(records, isToday, defaultInsight) {
  if (isToday && defaultInsight) {
    return defaultInsight;
  }
  if (!records || records.length === 0) {
    return "No hourly records available for this date.";
  }

  const daylightRecords = records.filter((r) => r.is_daylight);
  let bestStart = null;
  let bestEnd = null;
  let bestLen = 0;
  let curStart = null;
  let curLen = 0;

  for (const r of daylightRecords) {
    if (r.spray_safety === "optimal") {
      if (curStart === null) {
        curStart = r.display_time;
      }
      curLen += 1;
      if (curLen > bestLen) {
        bestLen = curLen;
        bestStart = curStart;
        bestEnd = r.display_time;
      }
    } else {
      curStart = null;
      curLen = 0;
    }
  }

  if (bestLen >= 2) {
    return `Optimal spraying window: ${bestStart} – ${bestEnd} (Low drift <10 km/h, Rain probability <30%).`;
  }
  if (bestLen === 1) {
    return `Narrow spraying window around ${bestStart}. Verify wind and rain conditions before application.`;
  }

  const rainUnsafe = daylightRecords.some((r) => r.spray_safety === "unsafe_rain");
  const windUnsafe = daylightRecords.some((r) => r.spray_safety === "unsafe_wind");
  if (rainUnsafe && windUnsafe) {
    return "Unfavorable spraying conditions: Rain wash-off and high wind drift expected.";
  }
  if (rainUnsafe) {
    return "Unfavorable spraying conditions: High rain wash-off risk expected.";
  }
  if (windUnsafe) {
    return "Chemical drift hazard: High wind speeds (>15 km/h) make daytime spraying unsafe.";
  }
  return "Marginal spraying conditions: Caution advised due to moderate wind or drizzle.";
}

/**
 * Returns effective 24-hour records for the target day with guaranteed non-null fallback.
 */
function getEffectiveRecords(data, selectedDate) {
  const forecastDays = data?.forecast || [];
  const todayDate = forecastDays[0]?.date;
  const targetDate = selectedDate || todayDate;
  const isToday = !targetDate || targetDate === todayDate;

  const liveHourly = data?.live_weather?.hourly;
  const liveRecords = liveHourly?.records;
  const allRecords = liveHourly?.all_records;

  // 1. If today and live rolling records starting at current hour are available
  if (isToday && Array.isArray(liveRecords) && liveRecords.length > 0) {
    return liveRecords.slice(0, 24);
  }

  // 2. If future day (or fallback today) and full 120h records are available
  if (Array.isArray(allRecords) && allRecords.length > 0) {
    const dayRecords = allRecords.filter((r) => r.time && r.time.startsWith(targetDate));
    if (dayRecords.length > 0) {
      return dayRecords.slice(0, 24);
    }
  }

  // 3. Fallback 1: Parallel arrays present without pre-formatted records
  if (liveHourly?.time && Array.isArray(liveHourly.time) && liveHourly.time.length > 0) {
    const matchingIndices = [];
    liveHourly.time.forEach((tStr, idx) => {
      if (!targetDate || tStr.startsWith(targetDate)) {
        matchingIndices.push(idx);
      }
    });

    const indicesToUse =
      matchingIndices.length > 0
        ? matchingIndices.slice(0, 24)
        : liveHourly.time.slice(0, 24).map((_, i) => i);

    return indicesToUse.map((idx) => {
      const tStr = liveHourly.time[idx];
      const dtHour = parseInt(tStr.split("T")[1]?.split(":")[0] || "12", 10);
      const displayTime = `${dtHour % 12 || 12} ${dtHour < 12 ? "AM" : "PM"}`;
      const tempVal = liveHourly.temperature_2m?.[idx] ?? 28;
      const probVal = liveHourly.precipitation_probability?.[idx] ?? 0;
      const rainVal = liveHourly.precipitation?.[idx] ?? 0;
      const windVal = liveHourly.wind_speed_10m?.[idx] ?? 5;
      const codeVal = liveHourly.weather_code?.[idx] ?? 1;

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

  // 4. Fallback 2: Synthesize diurnal curve from the selected day's baseline forecast
  const activeDay = forecastDays.find((d) => d.date === targetDate) || forecastDays[0];
  const tmax = activeDay?.tmax_c?.p50 ?? (typeof activeDay?.tmax_c === "number" ? activeDay?.tmax_c : 32);
  const tmin = activeDay?.tmin_c ?? 24;
  const probVal = Math.round((activeDay?.rain_probability ?? 0) * 100);
  const rainMm = activeDay?.rain_mm?.p50 ?? (typeof activeDay?.rain_mm === "number" ? activeDay?.rain_mm : 0);
  const datePrefix = targetDate || "2026-09-11";

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
      time: `${datePrefix}T${String(h).padStart(2, "0")}:00`,
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

export default function HourlyWeatherSlider({
  data,
  selectedDate,
  onSelectDate,
  onToggleLive,
}) {
  const [activeTab, setActiveTab] = useState("temperature");

  const forecastDays = data?.forecast || [];
  const todayDate = forecastDays[0]?.date;
  const effectiveDate = selectedDate || todayDate;
  const selectedDayIndex = forecastDays.findIndex((d) => d.date === effectiveDate);
  const isToday = selectedDayIndex <= 0;

  const dayLabel =
    selectedDayIndex === 0
      ? "Today"
      : selectedDayIndex === 1
      ? "Tomorrow"
      : selectedDayIndex > 1
      ? `Day +${selectedDayIndex}`
      : "Selected Day";

  const formattedSelectedDate = formatForecastDate(effectiveDate);

  const records = getEffectiveRecords(data, effectiveDate);
  const liveWeather = data?.live_weather;
  const isDynamic = data?.is_live_dynamic ?? false;
  const operationalInsight = computeOperationalInsight(
    records,
    isToday,
    liveWeather?.operational_insight
  );
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
            24-hour hour-by-hour forecast and spraying recommendations for{" "}
            <strong>{dayLabel}</strong>
            {formattedSelectedDate ? ` (${formattedSelectedDate})` : ""}
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

          <div className="hourly-tabs" role="tablist" aria-label="Metric Views">
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

      {/* Forecast Day Selector Navigation Bar */}
      {forecastDays.length > 1 && (
        <div className="hourly-day-bar">
          <div className="hourly-day-bar-title">
            <span className="day-bar-icon">📅</span>
            <span>Select Day:</span>
          </div>
          <div className="hourly-day-pills" role="tablist" aria-label="Select Forecast Day">
            {forecastDays.map((day, idx) => {
              const isSelected = effectiveDate === day.date;
              const title = idx === 0 ? "Today" : idx === 1 ? "Tomorrow" : `Day +${idx}`;
              const dateText = formatForecastDate(day.date);
              return (
                <button
                  key={day.date}
                  type="button"
                  role="tab"
                  aria-selected={isSelected}
                  className={`hourly-day-pill ${isSelected ? "active" : ""}`}
                  onClick={() => onSelectDate && onSelectDate(day.date)}
                  title={`View hourly forecast for ${title} (${dateText})`}
                >
                  <span className="pill-title">{title}</span>
                  <span className="pill-date">{dateText}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Horizontal Scrollable Slider */}
      <div className="hourly-scroll-container">
        <div className="hourly-track">
          {records.map((rec, idx) => {
            const isNow = isToday && idx === 0;
            const timeLabel = isNow ? "Now" : rec.display_time;
            const badge = getSprayBadgeInfo(rec.spray_safety);

            return (
              <div
                key={rec.time || idx}
                className={`hourly-cell ${isNow ? "current-hour" : ""} ${
                  rec.is_daylight ? "daylight" : "nighttime"
                }`}
              >
                {/* Time */}
                <div className="hourly-cell-time">{timeLabel}</div>

                {/* Weather Icon (Self-contained SVG - zero broken images) */}
                <div className="hourly-cell-icon-wrap">
                  <WeatherIcon
                    code={rec.weather_code}
                    isDaylight={rec.is_daylight}
                    className="hourly-cell-icon"
                    size={32}
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
              <strong>🚜 {dayLabel.toUpperCase()}&apos;S FARM WORK ADVICE</strong>
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
