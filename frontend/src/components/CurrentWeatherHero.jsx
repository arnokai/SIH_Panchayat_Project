/**
 * CurrentWeatherHero.jsx
 *
 * Farmer-friendly Hero Weather Card providing:
 * 1. Plain-English local temperature and weather condition.
 * 2. 4 intuitive agricultural weather metrics (Rainfall, Rain Chance, Air Moisture, Wind).
 * 3. 3-card Farmer Quick-Action Bar (Spraying safety, Irrigation/Fertilizer, Field Drainage).
 * 4. Crop-specific agronomic safety tip banner (Paddy vs Vegetables).
 */

function getRainCategory(p50, p10, p90) {
  const hasRange = p10 != null && p90 != null && (p90 - p10 > 0.2);
  const rangeStr = hasRange ? ` (${p10.toFixed(1)} – ${p90.toFixed(1)} mm range)` : "";

  if (p50 == null || p50 <= 0.1) {
    return "Dry / No rain expected";
  }
  if (p50 < 2.5) {
    return `Light Drizzle${rangeStr}`;
  }
  if (p50 < 15.0) {
    return `Moderate Rain${rangeStr}`;
  }
  if (p50 < 35.0) {
    return `Heavy Rain${rangeStr}`;
  }
  return `Very Heavy Downpour${rangeStr}`;
}

function getRainProbText(prob) {
  if (prob >= 0.7) return "Very High Chance Today";
  if (prob >= 0.4) return "Moderate Chance of Rain";
  if (prob >= 0.15) return "Slight Chance of Rain";
  return "Clear & Dry Forecast";
}

function getMoistureText(humidity) {
  if (humidity >= 85) return "High Moisture (Fungal Disease Risk)";
  if (humidity >= 65) return "Favorable Crop Moisture";
  return "Dry Air (Increased Water Loss)";
}

function getWindText(windKmh) {
  if (windKmh >= 18) return "Strong Breeze (Chemical Drift Hazard)";
  if (windKmh >= 12) return "Moderate Breeze (Spray With Caution)";
  return "Gentle Breeze (Safe for Farm Work)";
}

function getFarmerQuickActions(p50, rainProb, humidity, windKmh, crop) {
  // 1. Chemical Spraying Decision
  let sprayAction = {
    title: "Pesticide & Spraying",
    status: "success",
    badge: "✓ Safe to Spray",
    tip: "Good wind & dry canopy. Best application window in early daylight.",
  };
  if (p50 >= 0.2 || rainProb >= 0.5) {
    sprayAction = {
      title: "Pesticide & Spraying",
      status: "danger",
      badge: "🚫 Avoid Today",
      tip: "Rain will wash off chemicals and waste money. Wait for a dry day.",
    };
  } else if (windKmh >= 16) {
    sprayAction = {
      title: "Pesticide & Spraying",
      status: "danger",
      badge: "🚫 High Wind Drift",
      tip: "Wind speed > 15 km/h causes spray drift onto neighboring plots.",
    };
  } else if (windKmh >= 11 || rainProb >= 0.3) {
    sprayAction = {
      title: "Pesticide & Spraying",
      status: "warning",
      badge: "⚠️ Spray with Caution",
      tip: "Light wind or chance of drizzle. Use drift-reduction nozzles.",
    };
  }

  // 2. Field Irrigation & Fertilizer Top-Dressing
  let irrigateAction = {
    title: "Irrigation & Fertilizer",
    status: "success",
    badge: "🚜 Safe to Irrigate / Feed",
    tip: "Apply routine irrigation and urea top-dressing as scheduled.",
  };
  if (p50 >= 5.0) {
    irrigateAction = {
      title: "Irrigation & Fertilizer",
      status: "warning",
      badge: "⏸️ Postpone Today",
      tip: "Upcoming rain will water the crops; fertilizer applied now will run off.",
    };
  } else if (p50 >= 1.0) {
    irrigateAction = {
      title: "Irrigation & Fertilizer",
      status: "info",
      badge: "💧 Light Watering Only",
      tip: "Drizzle will provide light moisture. Irrigate only sandy/dry patches.",
    };
  }

  // 3. Drainage & Crop Protection
  let cropAction;
  if (crop === "paddy") {
    if (p50 >= 15.0) {
      cropAction = {
        title: "Paddy Water Management",
        status: "danger",
        badge: "⚠️ Clear Field Outlets",
        tip: "Heavy downpour expected. Clear drainage pipes to prevent submergence above 5 cm.",
      };
    } else if (p50 >= 5.0) {
      cropAction = {
        title: "Paddy Water Management",
        status: "info",
        badge: "🌾 Store Fresh Rainwater",
        tip: "Rain is beneficial. Strengthen field bunds to store fresh rainwater in paddy plots.",
      };
    } else {
      cropAction = {
        title: "Paddy Water Management",
        status: "success",
        badge: "🌾 Maintain Standing Water",
        tip: "Keep 2–3 cm shallow standing water to protect roots and suppress weed growth.",
      };
    }
  } else {
    // vegetables
    if (p50 >= 5.0) {
      cropAction = {
        title: "Vegetable Field Protection",
        status: "danger",
        badge: "🚨 Clear Furrows Immediately",
        tip: "Vegetables cannot tolerate standing water. Open trenches to prevent root rot.",
      };
    } else if (humidity >= 80) {
      cropAction = {
        title: "Vegetable Field Protection",
        status: "warning",
        badge: "⚠️ Scout for Leaf Blight",
        tip: "Humid air triggers fungal disease. Inspect lower leaves for spots and mildew.",
      };
    } else {
      cropAction = {
        title: "Vegetable Field Protection",
        status: "success",
        badge: "🥬 Favorable Field Conditions",
        tip: "Good aeration and soil temperature for transplanting and weeding.",
      };
    }
  }

  return [sprayAction, irrigateAction, cropAction];
}

export default function CurrentWeatherHero({
  data,
  selectedCrop,
  onCropChange,
  isLive,
  onToggleLive,
}) {
  if (!data) return null;

  const today = data.forecast?.[0];
  const liveCur = data.live_weather?.current;

  // Day/night status and icon selection
  const currentHour = new Date().getHours();
  const isNight = currentHour < 6 || currentHour >= 18;

  const rainProb = today?.rain_probability ?? 0;
  const p10 = today?.rain_mm?.p10 ?? 0;
  const p50 = today?.rain_mm?.p50 ?? 0;
  const p90 = today?.rain_mm?.p90 ?? 0;
  const humidity = liveCur?.relative_humidity_2m ?? 82;
  const windKmh = liveCur?.wind_speed_10m ?? 8;

  const isRainy = (liveCur?.precipitation > 0) || (liveCur?.weather_code >= 50) || (rainProb > 0.6);
  const isCloudy = (liveCur?.weather_code != null && liveCur.weather_code > 0) || (rainProb > 0.3);

  const conditionText = isRainy
    ? "Rainy / Wet Conditions"
    : isCloudy
    ? (isNight ? "Partly Cloudy Night" : "Partly Cloudy Sky")
    : (isNight ? "Clear Night Sky" : "Sunny / Fair Weather");

  const weatherIconUrl = isRainy
    ? "https://ssl.gstatic.com/onebox/weather/64/rain.png"
    : isCloudy
    ? (isNight ? "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy_night.png" : "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy.png")
    : (isNight ? "https://ssl.gstatic.com/onebox/weather/64/night.png" : "https://ssl.gstatic.com/onebox/weather/64/sunny.png");

  const currentTemp = liveCur?.temperature_2m != null
    ? Math.round(liveCur.temperature_2m)
    : today?.tmax_c?.p50 != null
    ? (isNight ? Math.round(today.tmin_c != null ? today.tmin_c + 1.5 : today.tmax_c.p50 - 4) : Math.round(today.tmax_c.p50))
    : "--";

  const minTemp = today?.tmin_c != null ? Math.round(today.tmin_c) : "--";
  const maxTemp = today?.tmax_c?.p50 != null ? Math.round(today.tmax_c.p50) : "--";

  const quickActions = getFarmerQuickActions(p50, rainProb, humidity, windKmh, selectedCrop);

  return (
    <section className="weather-hero-card">
      {/* Location, Crop Context & Dynamic Stream Header */}
      <div className="hero-top-bar">
        <div className="hero-location">
          <span className="hero-pin">📍</span>
          <div>
            <h2 className="hero-gp-name">{data.panchayat_name}</h2>
            <p className="hero-sub-location">
              {data.block_name ? `${data.block_name.toUpperCase()} BLOCK` : ""}
              {data.district_name ? ` • ${data.district_name.toUpperCase()} DISTRICT` : ""}
            </p>
          </div>
        </div>

        <div className="hero-controls">
          {/* Crop Selector Switcher */}
          <div className="hero-crop-toggle">
            <span className="control-label">SELECT CROP:</span>
            <div className="crop-pill-group">
              <button
                type="button"
                className={`crop-pill ${selectedCrop === "paddy" ? "active" : ""}`}
                onClick={() => onCropChange("paddy")}
              >
                🌾 Paddy
              </button>
              <button
                type="button"
                className={`crop-pill ${selectedCrop === "vegetables" ? "active" : ""}`}
                onClick={() => onCropChange("vegetables")}
              >
                🥬 Vegetables
              </button>
            </div>
          </div>

          {/* Dynamic / Live Mode Toggle */}
          <div className="hero-mode-toggle">
            <button
              type="button"
              className={`mode-toggle-btn ${isLive ? "live" : "offline"}`}
              onClick={onToggleLive}
              title={isLive ? "Click to switch to offline baseline" : "Click to switch to live Open-Meteo stream"}
            >
              <span className="mode-dot"></span>
              <span>{isLive ? "Live (ECMWF/GFS)" : "Offline Baseline"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Temperature & Visual Condition Row */}
      <div className="hero-main-weather">
        <div className="hero-temp-display">
          <img src={weatherIconUrl} alt={conditionText} className="hero-weather-icon" />
          <div className="hero-temp-numbers">
            <span className="hero-temp-large">{currentTemp}</span>
            <span className="hero-temp-unit">°C</span>
          </div>
          <div className="hero-temp-range">
            <span>High: <strong>{maxTemp}°C</strong></span>
            <span>Low: <strong>{minTemp}°C</strong></span>
          </div>
        </div>

        <div className="hero-condition-summary">
          <div className="hero-condition-title">{conditionText}</div>
          <div className="hero-source-tag">
            <span>Forecast Source: <strong>{data.source || "Open-Meteo Dynamic"}</strong></span>
            <span> • Panchayat Model: {data.model_version || "TerraMind V2"}</span>
          </div>
        </div>

        {/* 4 Farmer-Friendly Weather Telemetry Cards */}
        <div className="hero-metrics-grid">
          <div className="metric-cell">
            <span className="metric-label">🌧️ Expected Rainfall</span>
            <span className="metric-value">
              {p50 != null ? `${p50.toFixed(1)} mm` : "--"}
            </span>
            <span className="metric-sub">
              {getRainCategory(p50, p10, p90)}
            </span>
          </div>

          <div className="metric-cell">
            <span className="metric-label">☂️ Chance of Rain</span>
            <span className="metric-value">
              {Math.round(rainProb * 100)}%
            </span>
            <span className="metric-sub">
              {getRainProbText(rainProb)}
            </span>
          </div>

          <div className="metric-cell">
            <span className="metric-label">💧 Air Moisture</span>
            <span className="metric-value">
              {Math.round(humidity)}%
            </span>
            <span className="metric-sub">
              {getMoistureText(humidity)}
            </span>
          </div>

          <div className="metric-cell">
            <span className="metric-label">💨 Wind Speed</span>
            <span className="metric-value">
              {Math.round(windKmh)} km/h
            </span>
            <span className="metric-sub">
              {getWindText(windKmh)}
            </span>
          </div>
        </div>
      </div>

      {/* Farmer Quick-Action Decision Cards */}
      <div className="farmer-quick-actions-box">
        <div className="quick-actions-header">
          <span className="quick-actions-title">⚡ QUICK FARM WORK DECISIONS (TODAY)</span>
          <span className="quick-actions-sub">Plain advice for immediate field operations</span>
        </div>
        <div className="quick-actions-grid">
          {quickActions.map((action, idx) => (
            <div key={idx} className={`quick-action-card status-${action.status}`}>
              <div className="quick-action-top">
                <span className="quick-action-category">{action.title}</span>
                <span className={`quick-action-badge badge-${action.status}`}>{action.badge}</span>
              </div>
              <p className="quick-action-tip">{action.tip}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Crop Guidance Callout */}
      <div className="crop-guidance-banner">
        <span className="crop-guidance-icon">{selectedCrop === "paddy" ? "🌾" : "🥬"}</span>
        <div className="crop-guidance-text">
          <strong>
            {selectedCrop === "paddy" ? "Paddy Crop Management Tip:" : "Vegetables Management Tip:"}
          </strong>{" "}
          {selectedCrop === "paddy"
            ? "Rice crops thrive with shallow standing water (2–3 cm). Check field bunds to retain rainwater, but open drainage channels if heavy showers exceed 5 cm depth to prevent tiller decay."
            : "Vegetable plots are sensitive to standing water and high air humidity. Maintain raised beds, clear drainage furrows before showers, and scout for early leaf blight or fungal mildew."}
        </div>
      </div>
    </section>
  );
}
