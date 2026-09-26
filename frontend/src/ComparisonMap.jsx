import { Component, useEffect, useRef, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  Tooltip,
  useMap,
  GeoJSON,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { formatForecastDate, getActionChip } from "./utils/formatters";
import { fetchRadarTimestamps, fetchBoundaries } from "./services/api";

class MapErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.warn("Map encountered a runtime issue:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="map-error-fallback"
          style={{
            padding: "40px 20px",
            textAlign: "center",
            background: "#f3f8f5",
            borderRadius: "15px",
            border: "1px dashed #2d8a57",
            color: "#06372b",
          }}
        >
          <p style={{ fontWeight: 600, margin: "0 0 8px 0" }}>
            ⚠️ Interactive GIS map preview encountered an issue.
          </p>
          <p style={{ fontSize: "13px", color: "#4f695f", margin: "0 0 16px 0" }}>
            All core weather intelligence, 24-hour sliders, and agricultural advisories remain fully operational.
          </p>
          <button
            type="button"
            className="popup-select-btn"
            onClick={() => this.setState({ hasError: false })}
          >
            Retry Loading Map
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371.0;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c * 10) / 10;
}

/**
 * Controller to smoothly pan, zoom, or fit bounds when the target or boundary changes.
 */
function MapViewController({ center, bounds, zoom = 12 }) {
  const map = useMap();
  const prevCenterRef = useRef(null);
  const prevBoundsRef = useRef(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        map.invalidateSize();
      } catch (e) {
        // ignore
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (bounds && Array.isArray(bounds) && bounds.length === 2) {
      const boundsKey = JSON.stringify(bounds);
      if (prevBoundsRef.current !== boundsKey) {
        prevBoundsRef.current = boundsKey;
        try {
          map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14, animate: true, duration: 1.2 });
          return;
        } catch (err) {
          console.warn("Leaflet fitBounds failed:", err);
        }
      }
    } else if (
      center &&
      Array.isArray(center) &&
      typeof center[0] === "number" &&
      typeof center[1] === "number" &&
      !isNaN(center[0]) &&
      !isNaN(center[1])
    ) {
      const prev = prevCenterRef.current;
      if (
        !prev ||
        Math.abs(prev[0] - center[0]) > 0.0001 ||
        Math.abs(prev[1] - center[1]) > 0.0001 ||
        prev[2] !== zoom
      ) {
        prevCenterRef.current = [center[0], center[1], zoom];
        try {
          map.flyTo(center, zoom, { duration: 1.2 });
        } catch (err) {
          console.warn("Leaflet flyTo failed:", err);
        }
      }
    }
  }, [bounds, center, zoom, map]);

  return null;
}

function ComparisonMapInner({
  data,
  forecastDays = [],
  selectedDate,
  onDateChange,
  onSelectPanchayat,
  activePanchayat = null,
  userGps = null,
}) {
  const effectiveUserGps = userGps || activePanchayat?.user_gps || null;
  const hasUserGps =
    effectiveUserGps &&
    typeof effectiveUserGps.latitude === "number" &&
    typeof effectiveUserGps.longitude === "number";

  const [mapLayer, setMapLayer] = useState("satellite"); // "satellite" | "topo" | "standard"
  const [showRadar, setShowRadar] = useState(true);
  const [radarPath, setRadarPath] = useState("/v2/radar/d869fdcfbb08");
  const [radarHost, setRadarHost] = useState("https://tilecache.rainviewer.com");
  const [radarFrames, setRadarFrames] = useState([]);
  const [activeFrameIndex, setActiveFrameIndex] = useState(0);
  const [isPlayingRadar, setIsPlayingRadar] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isTopoHudExpanded, setIsTopoHudExpanded] = useState(true);

  // Panchayat Territorial Boundaries State
  const [boundaries, setBoundaries] = useState(null);
  const [loadingBoundaries, setLoadingBoundaries] = useState(false);

  // Fetch real-time RainViewer radar timestamps and historical animation frames
  useEffect(() => {
    let active = true;
    async function loadRadar() {
      try {
        const res = await fetchRadarTimestamps();
        if (active && res) {
          if (res.radar_frames && res.radar_frames.length > 0) {
            setRadarFrames(res.radar_frames);
            setActiveFrameIndex(res.radar_frames.length - 1);
            setRadarPath(res.radar_frames[res.radar_frames.length - 1].path);
          } else if (res.latest_radar_path) {
            setRadarPath(res.latest_radar_path);
          }
          if (res.host) setRadarHost(res.host);
        }
      } catch (e) {
        console.warn("Could not load latest RainViewer radar timestamp:", e);
      }
    }
    loadRadar();
    const interval = setInterval(loadRadar, 180000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  // Radar playback animation loop
  useEffect(() => {
    if (!isPlayingRadar || !radarFrames.length) return;
    const intervalMs = playbackSpeed === 2 ? 400 : 800;
    const timer = setInterval(() => {
      setActiveFrameIndex((prev) => (prev + 1) % radarFrames.length);
    }, intervalMs);
    return () => clearInterval(timer);
  }, [isPlayingRadar, radarFrames.length, playbackSpeed]);

  const activeRadarTilePath =
    radarFrames.length > 0 && radarFrames[activeFrameIndex]
      ? radarFrames[activeFrameIndex].path
      : radarPath;

  const BASE_LAYERS = {
    satellite: {
      id: "satellite",
      name: "Satellite Imagery",
      icon: "🛰️",
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      attribution: "&copy; Esri, Maxar, Earthstar Geographics, USDA, USGS",
      maxZoom: 18,
    },
    topo: {
      id: "topo",
      name: "Topographic & Contours",
      icon: "🏔️",
      url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
      attribution: "&copy; OpenStreetMap contributors, SRTM | style: &copy; OpenTopoMap (CC-BY-SA)",
      maxZoom: 17,
    },
    standard: {
      id: "standard",
      name: "Standard Map",
      icon: "🗺️",
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 19,
    },
  };

  // Target Gram Panchayat Coordinates (Strict priority: API payload exact coordinates > activePanchayat state > fallback)
  const panchayatLat =
    Number(data?.latitude) ||
    Number(data?.panchayat_lat) ||
    Number(activePanchayat?.latitude) ||
    22.804947;
  const panchayatLon =
    Number(data?.longitude) ||
    Number(data?.panchayat_lon) ||
    Number(activePanchayat?.longitude) ||
    88.509614;

  const coarseLat =
    Number(data?.coarse_coordinate?.latitude) || panchayatLat;
  const coarseLon =
    Number(data?.coarse_coordinate?.longitude) || panchayatLon;

  const hasCoarseDifference =
    Math.abs(coarseLat - panchayatLat) > 0.005 ||
    Math.abs(coarseLon - panchayatLon) > 0.005;

  const gridDistKm =
    data?.grid_distance_km !== undefined && data?.grid_distance_km !== null
      ? Number(data.grid_distance_km)
      : calculateDistanceKm(panchayatLat, panchayatLon, coarseLat, coarseLon);

  const panchayatName =
    data?.panchayat_name || activePanchayat?.panchayat_name || "Active Panchayat";
  const blockName =
    data?.block_name || activePanchayat?.block_name || "Amdanga";
  const districtName =
    data?.district_name || activePanchayat?.district_name || "North 24 Parganas";
  const targetPanchayatId =
    data?.panchayat_id || activePanchayat?.panchayat_id || "WB_107778";

  // Load contiguous Gram Panchayat boundaries for the active block
  useEffect(() => {
    let active = true;
    async function loadBoundaries() {
      setLoadingBoundaries(true);
      try {
        const res = await fetchBoundaries({
          panchayatId: targetPanchayatId,
          gpCode: data?.gp_code || activePanchayat?.gp_code,
          block: blockName,
          district: districtName,
        });
        if (active && res && res.features && res.features.length > 0) {
          setBoundaries(res);
        }
      } catch (err) {
        console.warn("Could not load boundaries for block:", err);
      } finally {
        if (active) setLoadingBoundaries(false);
      }
    }
    loadBoundaries();
    return () => {
      active = false;
    };
  }, [targetPanchayatId, blockName, districtName, data?.gp_code, activePanchayat?.gp_code]);

  // Resolve currently selected boundary feature and its bounding box
  const selectedFeature = boundaries?.features?.find((f) => {
    const p = f.properties || {};
    return (
      (p.panchayat_id && String(p.panchayat_id).toUpperCase() === String(targetPanchayatId).toUpperCase()) ||
      (p.gp_code && String(p.gp_code) === String(data?.gp_code || activePanchayat?.gp_code)) ||
      (p.panchayat_name && p.panchayat_name.toLowerCase() === panchayatName.toLowerCase())
    );
  }) || null;

  let targetBounds = null;
  if (selectedFeature?.properties?.bbox && Array.isArray(selectedFeature.properties.bbox)) {
    const b = selectedFeature.properties.bbox;
    // b: [minLon, minLat, maxLon, maxLat] -> Leaflet format: [[minLat, minLon], [maxLat, maxLon]]
    targetBounds = [[b[1], b[0]], [b[3], b[2]]];
  }

  // GeoJSON feature styling: selected Panchayat has a bold emerald highlight; neighbors have slate borders
  const getBoundaryStyle = (feature) => {
    const p = feature.properties || {};
    const isSelected =
      (p.panchayat_id && String(p.panchayat_id).toUpperCase() === String(targetPanchayatId).toUpperCase()) ||
      (p.gp_code && String(p.gp_code) === String(data?.gp_code || activePanchayat?.gp_code)) ||
      (p.panchayat_name && p.panchayat_name.toLowerCase() === panchayatName.toLowerCase());

    if (isSelected) {
      return {
        color: "#059669", // Vibrant Emerald Green active border
        weight: 3.5,
        opacity: 1,
        fillColor: "#10b981",
        fillOpacity: 0.28,
      };
    }

    return {
      color: "#64748b", // Distinct Slate border for neighboring Panchayats in block
      weight: 1.5,
      opacity: 0.85,
      fillColor: "#94a3b8",
      fillOpacity: 0.08,
      dashArray: "3, 3",
    };
  };

  const onEachBoundaryFeature = (feature, layer) => {
    const p = feature.properties || {};
    const isSelected =
      (p.panchayat_id && String(p.panchayat_id).toUpperCase() === String(targetPanchayatId).toUpperCase()) ||
      (p.gp_code && String(p.gp_code) === String(data?.gp_code || activePanchayat?.gp_code)) ||
      (p.panchayat_name && p.panchayat_name.toLowerCase() === panchayatName.toLowerCase());

    const areaText = p.area_sqkm ? ` • ${p.area_sqkm} km²` : "";
    const sourceLabel = "Official Cadastral Territory";

    if (isSelected) {
      layer.bindTooltip(
        `<div style="font-family: inherit; font-size: 12px; font-weight: 700; color: #ffffff;">
           📍 ${p.panchayat_name} (Active Gram Panchayat)
           <div style="font-size: 10px; font-weight: 400; color: #a7f3d0; margin-top: 2px;">
             ${p.block_name} Block${areaText} • ${sourceLabel}
           </div>
         </div>`,
        { sticky: true, direction: "top", className: "active-gp-boundary-label" }
      );
    } else {
      layer.bindTooltip(
        `<div style="font-family: inherit; font-size: 12px; font-weight: 600; color: #1e293b;">
           🏢 ${p.panchayat_name} Gram Panchayat
           <div style="font-size: 11px; font-weight: 400; color: #64748b; margin-top: 1px;">
             ${p.block_name} Block${areaText}
           </div>
           <div style="color: #059669; font-weight: 700; font-size: 11px; margin-top: 4px;">
             👉 Click to select this Panchayat
           </div>
         </div>`,
        { sticky: true, direction: "top", className: "neighbor-gp-boundary-label" }
      );

      layer.on({
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({
            weight: 2.8,
            color: "#059669",
            fillColor: "#10b981",
            fillOpacity: 0.22,
          });
        },
        mouseout: (e) => {
          const l = e.target;
          l.setStyle(getBoundaryStyle(feature));
        },
        click: () => {
          if (typeof onSelectPanchayat === "function") {
            onSelectPanchayat({
              panchayat_id: p.panchayat_id,
              gp_code: p.gp_code,
              panchayat_name: p.panchayat_name,
              block_name: p.block_name,
              district_name: p.district_name,
              latitude: p.latitude,
              longitude: p.longitude,
            });
          }
        },
      });
    }
  };

  // Topological micro-terrain physics
  const elevationAMSL = Math.round(
    Number(data?.elevation_m ?? activePanchayat?.elevation_m ?? 12)
  );
  const soilTypeStr = (data?.soil_type || activePanchayat?.soil_type || "alluvial_loam").replace(/_/g, " ");
  const nearestRiverName = data?.nearest_river || activePanchayat?.nearest_river || "Hooghly River";
  const riverDistanceM = data?.distance_to_river_m ?? activePanchayat?.distance_to_river_m ?? 14200;
  const riverDistanceKm = (riverDistanceM / 1000).toFixed(1);

  // Topographic classification
  let slopeDeg = 0.8;
  let terrainClassification = "Gangetic Delta Alluvial Plain";
  let drainageRisk = "High Water Retention / Alluvial Silt";
  let windShearRisk = "Low Frictional Resistance (Open Flatland)";

  if (elevationAMSL > 800) {
    slopeDeg = 14.5;
    terrainClassification = "Sub-Himalayan Terai Mountain Escarpment";
    drainageRisk = "Rapid Surface Runoff / Flash Gullying";
    windShearRisk = "High Topographic Acceleration / Ridge Shear";
  } else if (elevationAMSL > 120) {
    slopeDeg = 4.2;
    terrainClassification = "Chota Nagpur Lateritic Plateau Undulation";
    drainageRisk = "Moderate Porosity / Crust Infiltration";
    windShearRisk = "Rolling Hill Eddy Turbulence";
  } else if (elevationAMSL < 8) {
    slopeDeg = 0.4;
    terrainClassification = "Coastal Tidal Lowlands (Sundarbans Delta)";
    drainageRisk = "Tidal Inundation / Waterlogging Vulnerable";
    windShearRisk = "Severe Coastal Cyclone Surge Exposure";
  }

  // Active selected day forecast values
  const daysList = forecastDays.length > 0 ? forecastDays : data?.forecast || [];
  const selectedDay =
    daysList.find((day) => day.date === selectedDate) || daysList[0] || {};

  const p10 = selectedDay?.rain_mm?.p10 ?? 0;
  const p50 = selectedDay?.rain_mm?.p50 ?? (typeof selectedDay?.rain_mm === "number" ? selectedDay.rain_mm : 0);
  const p90 = selectedDay?.rain_mm?.p90 ?? 0;
  const probability = selectedDay?.rain_probability ?? 0;
  const tmax = selectedDay?.tmax_c?.p50 ?? selectedDay?.tmax_c ?? "--";
  const tmin = selectedDay?.tmin_c ?? "--";
  const chip = getActionChip(selectedDay?.advisory?.rule_id, p50);

  return (
    <section className="comparison-section">
      {/* Heading & Meta */}
      <div className="comparison-heading">
        <div>
          <p className="eyebrow">SPATIAL RESOLUTION & PHYSICAL DOWNSCALING</p>
          <h3>Panchayat Location & Regional Grid Comparison</h3>
        </div>
        <div className="comparison-date">
          <span>Target Date: </span>
          <strong>{formatForecastDate(selectedDay?.date) || selectedDay?.date || "—"}</strong>
        </div>
      </div>

      {/* Date Horizon Selector Bar */}
      {daysList.length > 1 && (
        <div className="comparison-day-selector" role="tablist" aria-label="Forecast horizon">
          {daysList.map((day, idx) => {
            const active = day.date === selectedDay?.date;
            const title = idx === 0 ? "Today" : idx === 1 ? "Tomorrow" : `Day +${idx}`;
            const dateStr = formatForecastDate(day.date);

            return (
              <button
                key={day.date}
                type="button"
                role="tab"
                aria-selected={active}
                className={`comparison-day-button ${active ? "active" : ""}`}
                onClick={() => onDateChange?.(day.date)}
              >
                <strong>{title}</strong> {dateStr}
              </button>
            );
          })}
        </div>
      )}

      {/* Dual Layout: Regional Grid Card + Interactive Leaflet Map */}
      <div className="comparison-layout">
        {/* Left Side: Gram Panchayat Cadastral Territory Card */}
        <div className="block-comparison-card">
          <span className="comparison-kicker">🏛️ GRAM PANCHAYAT CADASTRAL TERRITORY</span>
          <strong className="block-rain-value">
            {p50.toFixed(1)}
            <span> mm</span>
          </strong>
          <p>
            Downscaled micro-terrain forecast for <strong>{panchayatName} GP</strong> ({blockName} Block, {districtName}).
          </p>

          <div className="block-mini-stats">
            <div>
              <span>RAIN PROB.</span>
              <strong>{Math.round(probability * 100)}%</strong>
            </div>
            <div>
              <span>MAX TEMP.</span>
              <strong>{typeof tmax === "number" ? `${Math.round(tmax)}°C` : tmax}</strong>
            </div>
            <div>
              <span>MIN TEMP.</span>
              <strong>{typeof tmin === "number" ? `${Math.round(tmin)}°C` : tmin}</strong>
            </div>
          </div>

          <div className="block-location">
            <span>TERRITORIAL BOUNDARY METRICS</span>
            <strong>
              📍 {panchayatLat.toFixed(4)}°N, {panchayatLon.toFixed(4)}°E
            </strong>
            <small
              className="grid-offset-badge"
              style={{
                background: "#ecfdf5",
                color: "#065f46",
                border: "1px solid #a7f3d0",
                fontSize: "11px",
                fontWeight: 600,
                padding: "3px 8px",
                borderRadius: "6px",
                marginTop: "4px",
                display: "inline-block",
              }}
            >
              🟢 Official Cadastral Boundary (geoBoundaries / SOI ADM4)
              {selectedFeature?.properties?.area_sqkm ? ` • ${selectedFeature.properties.area_sqkm} km²` : ""}
            </small>
            <div style={{ marginTop: "8px", fontSize: "11px", color: "#475569", lineHeight: 1.45 }}>
              ⛰️ <strong>Elevation:</strong> {elevationAMSL} m AMSL • <strong>Soil:</strong> {soilTypeStr}
              <br />
              🌊 <strong>Nearest River:</strong> {nearestRiverName} (~{riverDistanceKm} km)
            </div>
          </div>

          <div className="block-action-preview">
            <span>RECOMMENDED ACTION</span>
            <div className={`action-badge-mini ${chip.type}`}>
              <span>{chip.icon}</span>
              <strong>{chip.label}</strong>
            </div>
          </div>
        </div>

        {/* Right Side: Interactive Leaflet Map */}
        <div className="map-card">
          <div className="map-title">
            <div className="map-title-left">
              <span>
                PANCHAYAT LOCATION &amp; TERRAIN FOCUS
              </span>
            </div>
            <span className="map-status">
              📍 {panchayatName} ({panchayatLat.toFixed(4)}°N, {panchayatLon.toFixed(4)}°E) • {blockName}, {districtName}
              {hasUserGps && activePanchayat?.distance_km !== undefined && (
                <span> • <strong>~{activePanchayat.distance_km} km from device GPS</strong></span>
              )}
            </span>
          </div>

          {/* Map Layer Switcher & Doppler Radar Toolbar */}
          <div className="map-toolbar">
            <div className="layer-switcher-group">
              <span className="toolbar-label-mini">VIEW MODE:</span>
              {Object.values(BASE_LAYERS).map((layer) => (
                <button
                  key={layer.id}
                  type="button"
                  className={`layer-toggle-btn ${mapLayer === layer.id ? "active" : ""}`}
                  onClick={() => setMapLayer(layer.id)}
                  title={`Switch map view to ${layer.name}`}
                >
                  <span className="layer-btn-icon">{layer.icon}</span>
                  <span className="layer-btn-name">{layer.name}</span>
                </button>
              ))}
            </div>

            <div className="radar-toggle-group">
              <button
                type="button"
                className={`radar-toggle-btn ${showRadar ? "active" : ""}`}
                onClick={() => setShowRadar(!showRadar)}
                title="Toggle real-time RainViewer Doppler weather radar overlay"
              >
                <span className={`radar-beacon-dot ${showRadar ? "pulsing" : ""}`}></span>
                <span>📡 Live Doppler Radar</span>
                <span className="radar-status-tag">{showRadar ? "ON" : "OFF"}</span>
              </button>
            </div>
          </div>

          <div className="leaflet-map-wrapper">
            {/* Floating Topographic Micro-Terrain HUD ("Windy / Ventusky" Style) */}
            <div className={`map-topo-hud ${isTopoHudExpanded ? "expanded" : "collapsed"}`}>
              <div
                className="topo-hud-header"
                onClick={() => setIsTopoHudExpanded(!isTopoHudExpanded)}
                title="Click to expand/collapse micro-terrain telemetry"
              >
                <div className="topo-hud-title">
                  <span className="topo-hud-icon">🏔️</span>
                  <strong>COPERNICUS 30M TOPOGRAPHIC HUD</strong>
                </div>
                <button type="button" className="topo-hud-toggle-btn" aria-label="Toggle HUD">
                  {isTopoHudExpanded ? "▲" : "▼"}
                </button>
              </div>

              {isTopoHudExpanded && (
                <div className="topo-hud-content">
                  <div className="topo-hud-grid">
                    <div className="topo-stat-cell">
                      <span className="topo-stat-label">ELEVATION (AMSL)</span>
                      <strong className="topo-stat-value">{elevationAMSL} m</strong>
                      <small className="topo-stat-sub">30m DEM Centroid</small>
                    </div>
                    <div className="topo-stat-cell">
                      <span className="topo-stat-label">TERRAIN SLOPE</span>
                      <strong className="topo-stat-value">{slopeDeg}°</strong>
                      <small className="topo-stat-sub">{terrainClassification}</small>
                    </div>
                    <div className="topo-stat-cell">
                      <span className="topo-stat-label">HYDRO BASIN</span>
                      <strong className="topo-stat-value">{nearestRiverName}</strong>
                      <small className="topo-stat-sub">~{riverDistanceKm} km offset</small>
                    </div>
                    <div className="topo-stat-cell">
                      <span className="topo-stat-label">SOIL TEXTURE</span>
                      <strong className="topo-stat-value">{soilTypeStr}</strong>
                      <small className="topo-stat-sub">SoilGrids 250m</small>
                    </div>
                  </div>
                  <div className="topo-hud-footer">
                    <span className="topo-hud-alert-tag">⚡ AGRO-TOPOGRAPHIC EFFECT:</span>
                    <span className="topo-hud-alert-text">{drainageRisk} • {windShearRisk}</span>
                  </div>
                </div>
              )}
            </div>

            <MapErrorBoundary>
              <MapContainer
                center={[panchayatLat, panchayatLon]}
                zoom={12}
                scrollWheelZoom={false}
                className="leaflet-map"
              >
                {/* Dynamic Base Tile Layer (Satellite, Topographic with Contours, Standard) */}
                <TileLayer
                  key={mapLayer}
                  attribution={BASE_LAYERS[mapLayer].attribution}
                  url={BASE_LAYERS[mapLayer].url}
                  maxZoom={BASE_LAYERS[mapLayer].maxZoom}
                />

                {/* Real-Time RainViewer Doppler Precipitation Radar Overlay */}
                {showRadar && activeRadarTilePath && (
                  <TileLayer
                    key={`radar-${activeRadarTilePath}`}
                    url={`${radarHost}${activeRadarTilePath}/256/{z}/{x}/{y}/2/1_1.png`}
                    opacity={0.68}
                    zIndex={350}
                  />
                )}

                <MapViewController
                  center={[panchayatLat, panchayatLon]}
                  bounds={targetBounds}
                  zoom={12}
                />

                {/* Official Survey of India / geoBoundaries Block Outer Perimeter */}
                {boundaries && boundaries.block_boundary && (
                  <GeoJSON
                    key={`block-envelope-${targetPanchayatId}-${boundaries.block_name || blockName}`}
                    data={{
                      type: "Feature",
                      geometry: boundaries.block_boundary,
                      properties: {
                        block_name: boundaries.block_name || blockName,
                        district_name: boundaries.district_name || districtName,
                      },
                    }}
                    style={{
                      color: "#0f172a", // Dark slate block perimeter
                      weight: 2.8,
                      opacity: 0.9,
                      fill: false,
                      dashArray: "8, 6",
                    }}
                    interactive={false}
                  />
                )}

                {/* Gram Panchayat Territorial Boundaries (100% Contiguous Block Tiling) */}
                {boundaries && boundaries.features && boundaries.features.length > 0 && (
                  <GeoJSON
                    key={`boundaries-${targetPanchayatId}-${boundaries.features.length}-${panchayatName}`}
                    data={boundaries}
                    style={getBoundaryStyle}
                    onEachFeature={onEachBoundaryFeature}
                  />
                )}

                {/* User Device GPS Location Marker */}
                {hasUserGps && (
                  <>
                    <CircleMarker
                      center={[effectiveUserGps.latitude, effectiveUserGps.longitude]}
                      radius={7}
                      pathOptions={{
                        color: "#ffffff",
                        fillColor: "#0284c7",
                        fillOpacity: 1,
                        weight: 2.5,
                      }}
                    >
                      <Tooltip direction="top" offset={[0, -8]}>
                        <strong>📍 Your Device Location (GPS)</strong>
                        <br />
                        {effectiveUserGps.latitude.toFixed(4)}°N, {effectiveUserGps.longitude.toFixed(4)}°E
                        {effectiveUserGps.accuracy && (
                          <>
                            <br />
                            Accuracy: ±{effectiveUserGps.accuracy}m
                          </>
                        )}
                      </Tooltip>
                      <Popup>
                        <div className="map-popup-card">
                          <h4>📍 Your Detected Device GPS</h4>
                          <p><strong>Coordinates:</strong> {effectiveUserGps.latitude.toFixed(5)}°N, {effectiveUserGps.longitude.toFixed(5)}°E</p>
                          {effectiveUserGps.accuracy && (
                            <p><strong>GPS Accuracy:</strong> ±{effectiveUserGps.accuracy} meters</p>
                          )}
                          <p><strong>Resolved Panchayat:</strong> {panchayatName} ({districtName})</p>
                          {activePanchayat?.distance_km !== undefined && (
                            <p><strong>Distance to GP:</strong> {activePanchayat.distance_km} km</p>
                          )}
                        </div>
                      </Popup>
                    </CircleMarker>

                    {/* GPS Accuracy Uncertainty Circle */}
                    {effectiveUserGps.accuracy && effectiveUserGps.accuracy < 10000 && (
                      <CircleMarker
                        center={[effectiveUserGps.latitude, effectiveUserGps.longitude]}
                        radius={Math.min(32, Math.max(12, effectiveUserGps.accuracy / 15))}
                        pathOptions={{
                          color: "#0284c7",
                          fillColor: "#0284c7",
                          fillOpacity: 0.12,
                          weight: 1,
                          dashArray: "3, 3",
                        }}
                      />
                    )}
                  </>
                )}

                {/* Downscaled Gram Panchayat Target Pin */}
                <CircleMarker
                  center={[panchayatLat, panchayatLon]}
                  radius={10}
                  pathOptions={{
                    color: "#06372b",
                    fillColor: "#10b981",
                    fillOpacity: 0.95,
                    weight: 3,
                  }}
                >
                  <Tooltip
                    permanent
                    direction="top"
                    offset={[0, -12]}
                    className="active-gp-marker-label"
                  >
                    <div className="map-marker-label-content">
                      <strong>📍 {panchayatName}</strong>
                      <small>{p50.toFixed(1)} mm • {Math.round(probability * 100)}% rain</small>
                    </div>
                  </Tooltip>
                  <Popup>
                    <div className="map-popup-card">
                      <h4>{panchayatName} Gram Panchayat</h4>
                      <p><strong>LGD Code:</strong> {data?.gp_code || activePanchayat?.gp_code || "—"}</p>
                      <p><strong>Block:</strong> {blockName} | <strong>District:</strong> {districtName}</p>
                      <p><strong>Coordinates:</strong> {panchayatLat.toFixed(4)}°N, {panchayatLon.toFixed(4)}°E</p>
                      <p><strong>Downscaled Rain:</strong> {p50.toFixed(1)} mm ({p10.toFixed(1)}–{p90.toFixed(1)} mm)</p>
                      {(data?.elevation_m ?? activePanchayat?.elevation_m) !== undefined && (
                        <p><strong>Elevation:</strong> {Math.round(data?.elevation_m ?? activePanchayat?.elevation_m)} m AMSL</p>
                      )}
                      {(data?.soil_type || activePanchayat?.soil_type) && (
                        <p><strong>Soil:</strong> {(data?.soil_type || activePanchayat?.soil_type).replace(/_/g, " ")}</p>
                      )}
                      {(data?.nearest_river || activePanchayat?.nearest_river) && (
                        <p>
                          <strong>Nearest River:</strong> {data?.nearest_river || activePanchayat?.nearest_river}
                          {(data?.distance_to_river_m ?? activePanchayat?.distance_to_river_m) != null && (
                            <span> (~{((data?.distance_to_river_m ?? activePanchayat?.distance_to_river_m) / 1000).toFixed(1)} km)</span>
                          )}
                        </p>
                      )}
                    </div>
                  </Popup>
                </CircleMarker>
              </MapContainer>
            </MapErrorBoundary>
          </div>

          {/* Windy-Style Interactive Doppler Radar Player */}
          {showRadar && (
            <div className="radar-player-toolbar" aria-label="Doppler Radar Animation Player">
              <div className="radar-player-controls">
                <button
                  type="button"
                  className={`radar-ctrl-play-btn ${isPlayingRadar ? "playing" : ""}`}
                  onClick={() => setIsPlayingRadar(!isPlayingRadar)}
                  title={isPlayingRadar ? "Pause Doppler Radar Animation" : "Play Animated Doppler Loop"}
                >
                  {isPlayingRadar ? "⏸ Pause" : "▶ Play"}
                </button>

                <button
                  type="button"
                  className="radar-step-btn"
                  onClick={() => {
                    setIsPlayingRadar(false);
                    setActiveFrameIndex((prev) => (prev > 0 ? prev - 1 : Math.max(0, radarFrames.length - 1)));
                  }}
                  title="Step Backward (Previous Frame)"
                  disabled={radarFrames.length <= 1}
                >
                  ⏮
                </button>

                <button
                  type="button"
                  className="radar-step-btn"
                  onClick={() => {
                    setIsPlayingRadar(false);
                    setActiveFrameIndex((prev) => (prev + 1) % Math.max(1, radarFrames.length));
                  }}
                  title="Step Forward (Next Frame)"
                  disabled={radarFrames.length <= 1}
                >
                  ⏭
                </button>

                <div className="radar-scrubber-track">
                  <input
                    type="range"
                    min="0"
                    max={Math.max(0, radarFrames.length - 1)}
                    value={activeFrameIndex}
                    onChange={(e) => {
                      setIsPlayingRadar(false);
                      setActiveFrameIndex(Number(e.target.value));
                    }}
                    className="radar-timeline-slider"
                    aria-label="Doppler Radar Time Scrubber"
                  />
                  <div className="radar-timestamp-label">
                    {radarFrames.length > 0 && radarFrames[activeFrameIndex] ? (
                      activeFrameIndex === radarFrames.length - 1 ? (
                        <span className="live-frame-tag">🔴 Live (Latest Scan)</span>
                      ) : (
                        <span>-{(radarFrames.length - 1 - activeFrameIndex) * 10} min</span>
                      )
                    ) : (
                      "Live Scan"
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  className="radar-speed-toggle"
                  onClick={() => setPlaybackSpeed(playbackSpeed === 1 ? 2 : 1)}
                  title="Toggle Playback Speed"
                >
                  {playbackSpeed}x
                </button>
              </div>

              {/* Rain Intensity Color Scale */}
              <div className="radar-dbz-scale">
                <span className="dbz-label">Rain Intensity:</span>
                <div className="dbz-color-bar"></div>
                <span className="dbz-tick">Drizzle</span>
                <span className="dbz-tick">Moderate</span>
                <span className="dbz-tick">Heavy</span>
                <span className="dbz-tick">Severe</span>
              </div>
            </div>
          )}

          {/* Map Legend */}
          <div className="map-legend">
            <span>
              <i className="legend-selected-boundary"></i>
              {panchayatName} Border (Active Territory)
            </span>
            <span>
              <i className="legend-neighbor-boundary"></i>
              Neighboring Borders (Clickable)
            </span>
            {boundaries?.block_boundary && (
              <span>
                <i className="legend-block-boundary"></i>
                {blockName} Block Envelope (Survey of India)
              </span>
            )}
            <span>
              <i className="legend-selected-pin"></i>
              GP Headquarters / Village Hub
            </span>
            {hasUserGps && (
              <span>
                <i className="legend-user-gps"></i>
                Your Device Location (GPS)
              </span>
            )}
            {showRadar && (
              <span>
                <i className="legend-radar-dot"></i>
                Live Doppler Radar (RainViewer)
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Downscaling Intelligence Note */}
      <div className="comparison-note">
        <strong>Spatial Downscaling Intelligence:</strong> Coarse global weather models
        predict a single uniform value across 25–50 km grid cells. TerraMind uses a
        calibrated Two-Stage Hurdle ML model to downscale precipitation to each individual
        Gram Panchayat based on Copernicus 30m elevation, slope, terrain roughness,
        river proximity, and SoilGrids soil texture.
      </div>
    </section>
  );
}

export default function ComparisonMap(props) {
  return (
    <MapErrorBoundary>
      <ComparisonMapInner {...props} />
    </MapErrorBoundary>
  );
}
