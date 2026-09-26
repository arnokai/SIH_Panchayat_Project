import { useState } from "react";
import WeatherIcon from "./WeatherIcon";
import { getCurrentSeason } from "../utils/seasons";

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
  } else if (crop === "potato") {
    if (p50 >= 15.0) {
      cropAction = {
        title: "Potato Furrow Drainage",
        status: "danger",
        badge: "🚨 Open Drainage Furrows",
        tip: "Potatoes cannot tolerate waterlogging. Clear furrows immediately to prevent tuber rot.",
      };
    } else if (humidity >= 82) {
      cropAction = {
        title: "Potato Blight Prevention",
        status: "warning",
        badge: "⚠️ Late Blight Alert",
        tip: "Cool, damp air triggers Phytophthora blight. Inspect foliage and prepare protective spray.",
      };
    } else {
      cropAction = {
        title: "Potato Crop Management",
        status: "success",
        badge: "🥔 Ideal Bulking Conditions",
        tip: "Cool, sunny days promote healthy tuber enlargement and root aeration.",
      };
    }
  } else if (crop === "mustard") {
    if (p50 >= 10.0) {
      cropAction = {
        title: "Mustard Field Drainage",
        status: "warning",
        badge: "⚠️ Avoid Standing Water",
        tip: "Mustard plants are sensitive to waterlogging. Ensure channels drain freely.",
      };
    } else if (humidity >= 75) {
      cropAction = {
        title: "Mustard Pest Alert",
        status: "warning",
        badge: "⚠️ Aphid & Rust Watch",
        tip: "Humid overcast conditions favor aphid colonies and white rust on leaves.",
      };
    } else {
      cropAction = {
        title: "Mustard Crop Growth",
        status: "success",
        badge: "🌼 Favorable Pod Filling",
        tip: "Dry weather promotes active pollinator activity and healthy pod maturation.",
      };
    }
  } else if (crop === "jute") {
    if (p50 >= 20.0) {
      cropAction = {
        title: "Jute Field Protection",
        status: "danger",
        badge: "🚨 Drain Flood Water",
        tip: "High risk of Macrophomina stem and root rot from standing water. Open field drains.",
      };
    } else if (p50 >= 5.0) {
      cropAction = {
        title: "Jute Stem Growth",
        status: "info",
        badge: "🌿 Vigorous Vegetative Phase",
        tip: "Warm monsoon showers promote rapid stem elongation and fiber development.",
      };
    } else {
      cropAction = {
        title: "Jute Crop Care",
        status: "success",
        badge: "🌿 Normal Fiber Growth",
        tip: "Maintain weed-free furrows and monitor soil moisture for young seedlings.",
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
  lastUpdated,
  isRefreshing,
  onRefresh,
}) {
  if (!data) return null;

  const today = data.forecast?.[0];
  const liveCur = data.live_weather?.current;

  const formattedUpdatedTime = lastUpdated
    ? new Intl.DateTimeFormat("en-IN", {
        hour: "numeric",
        minute: "numeric",
        second: "numeric",
        hour12: true,
      }).format(lastUpdated)
    : "Just now";

  // Day/night status and icon selection
  const currentHour = new Date().getHours();
  const isNight = currentHour < 6 || currentHour >= 18;

  const rainProb = today?.rain_probability ?? 0;
  const p10 = today?.rain_mm?.p10 ?? 0;
  const p50 = today?.rain_mm?.p50 ?? 0;
  const p90 = today?.rain_mm?.p90 ?? 0;
  const humidity = liveCur?.relative_humidity_2m ?? 82;
  const windKmh = liveCur?.wind_speed_10m ?? 8;
  const pressure = liveCur?.surface_pressure != null
    ? Math.round(liveCur.surface_pressure)
    : (liveCur?.pressure_msl != null ? Math.round(liveCur.pressure_msl) : 1004);
  const windDirDeg = liveCur?.wind_direction_10m ?? 210;
  const windGusts = liveCur?.wind_gusts_10m != null
    ? Math.round(liveCur.wind_gusts_10m)
    : Math.round(windKmh * 1.35);

  const getWindCardinal = (deg) => {
    const directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
    const idx = Math.round((deg % 360) / 22.5) % 16;
    return directions[idx];
  };
  const windCardinal = getWindCardinal(windDirDeg);

  const elevationM = Math.round(Number(data.elevation_m || 12));
  const nearestRiver = data.nearest_river || "Hooghly River";
  const riverDistKm = data.distance_to_river_m ? (data.distance_to_river_m / 1000).toFixed(1) : "14.2";

  const isRainy = (liveCur?.precipitation > 0) || (liveCur?.weather_code >= 50) || (rainProb > 0.6);
  const isCloudy = (liveCur?.weather_code != null && liveCur.weather_code > 0) || (rainProb > 0.3);

  const conditionText = isRainy
    ? "Rainy / Wet Conditions"
    : isCloudy
    ? (isNight ? "Partly Cloudy Night" : "Partly Cloudy Sky")
    : (isNight ? "Clear Night Sky" : "Sunny / Fair Weather");

  const currentWeatherCode = liveCur?.weather_code != null
    ? liveCur.weather_code
    : (isRainy ? 61 : isCloudy ? 2 : 0);

  const currentTemp = liveCur?.temperature_2m != null
    ? Math.round(liveCur.temperature_2m)
    : today?.tmax_c?.p50 != null
    ? (isNight ? Math.round(today.tmin_c != null ? today.tmin_c + 1.5 : today.tmax_c.p50 - 4) : Math.round(today.tmax_c.p50))
    : "--";

  const minTemp = today?.tmin_c != null ? Math.round(today.tmin_c) : "--";
  const maxTemp = today?.tmax_c?.p50 != null ? Math.round(today.tmax_c.p50) : "--";

  const quickActions = getFarmerQuickActions(p50, rainProb, humidity, windKmh, selectedCrop);

  const [speakingHero, setSpeakingHero] = useState(false);
  const [showOffSeason, setShowOffSeason] = useState(false);

  // Dynamic agro-ecological seasonal context
  const currentSeason = getCurrentSeason(new Date());
  const activeCrops = currentSeason.activeCrops;
  const inactiveCrops = currentSeason.inactiveCrops;
  const selectedIsOffSeason = inactiveCrops.some((c) => c.id === selectedCrop);
  const offSeasonReason = inactiveCrops.find((c) => c.id === selectedCrop)?.avoidanceReason;

  const handleSpeakHero = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Speech synthesis is not supported in this browser.");
      return;
    }
    if (speakingHero) {
      window.speechSynthesis.cancel();
      setSpeakingHero(false);
      return;
    }
    window.speechSynthesis.cancel();
    const gpName = data.panchayat_name || "Active Panchayat";
    const textToSpeak = `Today's weather advisory for ${gpName}, ${data.district_name || "West Bengal"}: Current temperature is ${currentTemp} degrees Celsius. ${conditionText}. Rain probability is ${Math.round(rainProb * 100)} percent. Air moisture is ${Math.round(humidity)} percent. Wind speed is ${Math.round(windKmh)} kilometers per hour. Today's advisory: ${today?.advisory?.text_en || "Normal agricultural field operations recommended."}`;
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = "en-IN";
    utterance.rate = 0.92;
    const voices = window.speechSynthesis.getVoices();
    const enVoice = voices.find(
      (v) => v.lang.startsWith("en") || v.name.toLowerCase().includes("english")
    );
    if (enVoice) utterance.voice = enVoice;
    utterance.onend = () => setSpeakingHero(false);
    utterance.onerror = () => setSpeakingHero(false);
    setSpeakingHero(true);
    window.speechSynthesis.speak(utterance);
  };

  const handleWhatsAppShare = () => {
    const gpName = data.panchayat_name || "Panchayat";
    const lines = [
      "🌾 *TerraMind Daily Panchayat Agro-Weather Bulletin* 🌾",
      `📍 *Panchayat:* ${gpName} (${data.district_name || "West Bengal"})`,
      `🌡️ *Current Temperature:* ${currentTemp}°C (${conditionText})`,
      `🌧️ *Rain Probability:* ${Math.round(rainProb * 100)}% (${getRainCategory(p50, p10, p90)})`,
      `💧 *Air Moisture:* ${Math.round(humidity)}% | 💨 *Wind Speed:* ${Math.round(windKmh)} km/h`,
      today?.advisory?.text_en ? `📢 *Advisory:* ${today.advisory.text_en}` : null,
      "",
      "🔗 _TerraMind — Panchayat-Scale Micro-Climate & Agro-Advisory Intelligence System_",
    ].filter(Boolean).join("\n");

    const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(lines)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <section className="weather-hero-card">
      {/* Degraded Offline Warning Banner if applicable */}
      {data.degraded && (
        <div className="degraded-banner">
          <strong>⚠️ Offline Prototype / Fallback Mode:</strong>{" "}
          <span>{data.degraded_reason || "Using cached offline baseline data."}</span>
        </div>
      )}

      {/* Location, Crop Context & Dynamic Stream Header */}
      <div className="hero-top-bar">
        <div className="hero-location">
          <span className="hero-pin">📍</span>
          <div>
            <h2 className="hero-gp-name">{data.panchayat_name}</h2>
            <p className="hero-sub-location">
              {data.gp_code ? <span className="hero-lgd-tag">LGD #{data.gp_code} • </span> : ""}
              {data.block_name ? `${data.block_name.toUpperCase()} BLOCK` : ""}
              {data.district_name ? ` • ${data.district_name.toUpperCase()} DISTRICT` : ""}
              {(data.panchayat_lat != null && data.panchayat_lon != null) || (data.latitude != null && data.longitude != null) ? (
                <span className="hero-coords-text">
                  {` • ${(data.panchayat_lat ?? data.latitude).toFixed(4)}°N, ${(data.panchayat_lon ?? data.longitude).toFixed(4)}°E`}
                </span>
              ) : null}
              {data.agro_climatic_zone ? ` • ${data.agro_climatic_zone.toUpperCase()}` : ""}
            </p>
          </div>
        </div>

        <div className="hero-controls">
          {/* Dynamic Seasonal Crop Selector (Auto-selects active season, avoids unnecessary crops) */}
          <div className="hero-crop-toggle">
            <div className="crop-label-row">
              <div className="season-info-badge">
                <span className="control-label">CURRENT SEASON:</span>
                <span className="season-badge" title={currentSeason.tagline}>
                  {currentSeason.icon} {currentSeason.name.toUpperCase()}
                </span>
                <span className="auto-selected-chip" title="Automatically filtered for local West Bengal agricultural calendar">
                  ✓ Active Season
                </span>
              </div>
              {data.phenology && (
                <span className="hero-phenology-tag">
                  🌱 <strong>{data.phenology.current_stage.toUpperCase()}</strong> ({data.phenology.accumulated_gdd} GDD)
                </span>
              )}
            </div>

            <div className="crop-pill-group">
              {/* Active Seasonal Crops (Auto-filtered) */}
              {activeCrops.map((c) => {
                const isActive = selectedCrop === c.id;
                return (
                  <button
                    key={c.id}
                    type="button"
                    className={`crop-pill ${isActive ? "active" : ""}`}
                    onClick={() => onCropChange(c.id)}
                    title={`${c.name} (${c.nameBn}) - ${c.tag}`}
                  >
                    <span>{c.icon} {c.name}</span>
                    {c.isPrimary && <span className="crop-primary-dot" title="Primary seasonal staple">•</span>}
                  </button>
                );
              })}

              {/* Show Off-Season Crops if toggled by user */}
              {showOffSeason &&
                inactiveCrops.map((c) => {
                  const isActive = selectedCrop === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      className={`crop-pill offseason ${isActive ? "active-offseason" : ""}`}
                      onClick={() => onCropChange(c.id)}
                      title={`Off-season: ${c.avoidanceReason}`}
                    >
                      <span>{c.icon} {c.name}</span>
                      <small className="offseason-subtag">(Off-Season)</small>
                    </button>
                  );
                })}

              {/* Off-season toggle button to avoid unnecessary ones by default */}
              <button
                type="button"
                className={`crop-offseason-toggle-btn ${showOffSeason ? "open" : ""}`}
                onClick={() => setShowOffSeason(!showOffSeason)}
                title={showOffSeason ? "Hide off-season crops to keep focus on active crops" : `Show ${inactiveCrops.length} off-season crops`}
              >
                {showOffSeason
                  ? "✕ Hide Off-Season"
                  : `+ Other Crops (${inactiveCrops.length} off-season)`}
              </button>
            </div>

            {/* If an off-season crop is selected, show an imperative agronomic warning */}
            {selectedIsOffSeason && (
              <div className="offseason-warning-card">
                <span className="warning-icon">⚠️</span>
                <div>
                  <strong>Off-Season Cropping Advisory ({selectedCrop.toUpperCase()}):</strong>
                  <p>{offSeasonReason}</p>
                </div>
              </div>
            )}
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

          {/* Real-time sync indicator & immediate manual refresh */}
          {onRefresh && (
            <div className="hero-sync-wrap">
              <button
                type="button"
                className={`hero-refresh-btn ${isRefreshing ? "refreshing" : ""}`}
                onClick={onRefresh}
                disabled={isRefreshing}
                title="Refresh real-time weather observations from Open-Meteo & rerun Hurdle ML downscaling"
              >
                <span className={`refresh-icon ${isRefreshing ? "spin" : ""}`}>🔄</span>
                <span>{isRefreshing ? "Syncing..." : "Sync Weather"}</span>
              </button>
              <span className="hero-last-updated" title="Live weather telemetry auto-syncs every 5 minutes">
                🕒 {formattedUpdatedTime}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Temperature & Visual Condition Row */}
      <div className="hero-main-weather">
        <div className="hero-temp-display">
          <WeatherIcon
            code={currentWeatherCode}
            isDaylight={!isNight}
            className="hero-weather-icon"
            size={60}
          />
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
            <span> • Panchayat Model: {data.model_version || "TerraMind"}</span>
            <span> • Stream: <strong className="live-status-pulse">🟢 Real-Time Auto-Synced</strong></span>
          </div>
        </div>

        {/* 6 Comprehensive Weather Telemetry Cards */}
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

          <div className="metric-cell">
            <span className="metric-label">🧭 Wind &amp; Gusts</span>
            <span className="metric-value">
              {windCardinal} ({windDirDeg}°)
            </span>
            <span className="metric-sub">
              Gusts up to {windGusts} km/h
            </span>
          </div>

          <div className="metric-cell">
            <span className="metric-label">⏲️ Air Pressure</span>
            <span className="metric-value">
              {pressure} hPa
            </span>
            <span className="metric-sub">
              {pressure < 1000 ? "⚠️ Low / Storm Inflow" : "Normal Atmospheric"}
            </span>
          </div>
        </div>

        {/* Location Micro-Terrain Topological Strip */}
        <div className="hero-topo-strip">
          <div className="hero-topo-title">
            <span>🏔️</span>
            <strong>LOCATION TOPOGRAPHIC PROFILE:</strong>
          </div>
          <div className="hero-topo-tags">
            <span className="hero-topo-tag">Elevation: <strong>{elevationM} m AMSL</strong></span>
            <span className="hero-topo-tag">River Basin: <strong>{nearestRiver} (~{riverDistKm} km)</strong></span>
            <span className="hero-topo-tag">SoilGrids: <strong>{(data.soil_type || "alluvial_loam").replace(/_/g, " ")}</strong></span>
            <span className="hero-topo-tag">Resolution: <strong>Copernicus 30m DEM</strong></span>
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
        <span className="crop-guidance-icon">
          {selectedCrop === "paddy"
            ? "🌾"
            : selectedCrop === "potato"
            ? "🥔"
            : selectedCrop === "mustard"
            ? "🌼"
            : selectedCrop === "jute"
            ? "🌿"
            : "🥬"}
        </span>
        <div className="crop-guidance-text">
          <strong>
            {selectedCrop === "paddy"
              ? "Paddy Crop Management Tip:"
              : selectedCrop === "potato"
              ? "Potato Crop Management Tip:"
              : selectedCrop === "mustard"
              ? "Mustard Crop Management Tip:"
              : selectedCrop === "jute"
              ? "Jute Crop Management Tip:"
              : "Vegetables Management Tip:"}
          </strong>{" "}
          {selectedCrop === "paddy"
            ? "Rice crops thrive with shallow standing water (2–3 cm). Check field bunds to retain rainwater, but open drainage channels if heavy showers exceed 5 cm depth to prevent tiller decay."
            : selectedCrop === "potato"
            ? "Potatoes require well-drained raised beds. Inspect for early Late Blight signs on leaf tips during cool humid fog, and never let water pool in furrows."
            : selectedCrop === "mustard"
            ? "Mustard is vulnerable to aphids during cloudy, humid weather at flowering. Ensure field drainage and inspect underside of leaves regularly."
            : selectedCrop === "jute"
            ? "Jute requires good soil moisture during vegetative elongation, but stagnant water at seedling stage causes fungal stem rot. Keep outlets cleared."
            : "Vegetable plots are sensitive to standing water and high air humidity. Maintain raised beds, clear drainage furrows before showers, and scout for early leaf blight or fungal mildew."}
        </div>
      </div>

      {/* Farmer Audio & WhatsApp Share Bar */}
      <div className="card-farmer-actions">
        <button
          type="button"
          className={`btn-action btn-voice ${speakingHero ? "is-speaking" : ""}`}
          onClick={handleSpeakHero}
          title="Listen to today's audio weather advisory"
        >
          <span className="action-icon">{speakingHero ? "⏹️" : "🔊"}</span>
          <span>{speakingHero ? "Stop Audio" : "Listen to Weather Audio"}</span>
        </button>

        <button
          type="button"
          className="btn-action btn-whatsapp"
          onClick={handleWhatsAppShare}
          title="Share daily weather and advisory on WhatsApp"
        >
          <span className="action-icon">💬</span>
          <span>Share on WhatsApp</span>
        </button>
      </div>
    </section>
  );
}
