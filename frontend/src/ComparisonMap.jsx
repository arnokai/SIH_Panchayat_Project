import { Component, useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { searchPanchayats } from "./services/api";
import { formatForecastDate, getActionChip } from "./utils/formatters";

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

/**
 * Controller to smoothly pan and zoom the Leaflet map when the target changes.
 */
function MapViewController({ center }) {
  const map = useMap();

  useEffect(() => {
    if (
      center &&
      Array.isArray(center) &&
      typeof center[0] === "number" &&
      typeof center[1] === "number" &&
      !isNaN(center[0]) &&
      !isNaN(center[1])
    ) {
      try {
        map.flyTo(center, 12, { duration: 1.0 });
      } catch (err) {
        console.warn("Leaflet flyTo failed:", err);
      }
    }
  }, [center, map]);

  return null;
}

function ComparisonMapInner({
  data,
  forecastDays = [],
  selectedDate,
  onDateChange,
  onSelectPanchayat,
  activePanchayat = null,
}) {
  const [neighborPanchayats, setNeighborPanchayats] = useState([]);
  const [loadingNeighbors, setLoadingNeighbors] = useState(false);

  // Active coordinates
  const activeLat =
    Number(data?.coarse_coordinate?.latitude) ||
    Number(activePanchayat?.latitude) ||
    22.804947;
  const activeLon =
    Number(data?.coarse_coordinate?.longitude) ||
    Number(activePanchayat?.longitude) ||
    88.509614;

  const currentPanchayatId =
    data?.panchayat_id ||
    activePanchayat?.panchayat_id ||
    (activePanchayat?.gp_code ? `WB_${activePanchayat.gp_code}` : "WB_107778");

  const blockName =
    data?.block_name || activePanchayat?.block_name || "Amdanga";
  const districtName =
    data?.district_name || activePanchayat?.district_name || "North 24 Parganas";

  // Fetch sibling Gram Panchayats in the active block or district
  useEffect(() => {
    let active = true;

    async function loadNeighbors() {
      if (!blockName && !districtName) return;
      setLoadingNeighbors(true);
      try {
        // Query by block name first
        let list = await searchPanchayats({ search: blockName, limit: 30 });
        if (!list || list.length === 0) {
          // Fallback to district query
          list = await searchPanchayats({ district: districtName, limit: 30 });
        }
        if (active && Array.isArray(list) && list.length > 0) {
          setNeighborPanchayats(list);
        }
      } catch (err) {
        console.warn("Could not load neighbor panchayats for spatial map:", err);
      } finally {
        if (active) setLoadingNeighbors(false);
      }
    }

    loadNeighbors();

    return () => {
      active = false;
    };
  }, [blockName, districtName]);

  // Combine markers ensuring current active panchayat is present
  const allMarkers = [...neighborPanchayats];
  const hasActive = allMarkers.some(
    (p) =>
      p.panchayat_id === currentPanchayatId ||
      String(p.gp_code) === String(activePanchayat?.gp_code)
  );

  if (!hasActive) {
    allMarkers.unshift({
      panchayat_id: currentPanchayatId,
      gp_code: activePanchayat?.gp_code || 107778,
      panchayat_name:
        data?.panchayat_name || activePanchayat?.panchayat_name || "Active Panchayat",
      block_name: blockName,
      district_name: districtName,
      latitude: activeLat,
      longitude: activeLon,
      elevation_m: data?.elevation_m,
      soil_type: data?.soil_type,
    });
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
          <p className="eyebrow">SPATIAL INTELLIGENCE & DOWN-SCALING</p>
          <h3>Spatial Forecast & Regional Comparison</h3>
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
        {/* Left Side: Regional Coarse Grid Card */}
        <div className="block-comparison-card">
          <span className="comparison-kicker">REGIONAL COARSE GRID (~25 KM)</span>
          <strong className="block-rain-value">
            {p50.toFixed(1)}
            <span> mm</span>
          </strong>
          <p>
            Regional atmospheric baseline from ECMWF/GFS ensemble prior to local
            topographic and soil physics downscaling.
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
            <span>REGIONAL GRID CENTROID</span>
            <strong>
              {activeLat.toFixed(4)}°N, {activeLon.toFixed(4)}°E
            </strong>
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
            <span>
              PANCHAYAT SPATIAL NETWORK ({blockName.toUpperCase()} BLOCK)
            </span>
            <span className="map-status">
              {loadingNeighbors ? "UPDATING MAP..." : `${allMarkers.length} PANCHAYATS ACTIVE`}
            </span>
          </div>

          <div className="leaflet-map-wrapper">
            <MapErrorBoundary>
              <MapContainer
                center={[activeLat, activeLon]}
                zoom={12}
                scrollWheelZoom={false}
                className="leaflet-map"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapViewController center={[activeLat, activeLon]} />

                {/* Sibling and Active Panchayat Markers */}
                {allMarkers.map((p, idx) => {
                  const lat = Number(p.latitude);
                  const lon = Number(p.longitude);
                  if (!lat || !lon || isNaN(lat) || isNaN(lon)) return null;

                  const isSelected =
                    p.panchayat_id === currentPanchayatId ||
                    String(p.gp_code) === String(activePanchayat?.gp_code);

                  return (
                    <CircleMarker
                      key={p.panchayat_id || (p.gp_code ? `gp-${p.gp_code}` : `marker-${idx}`)}
                      center={[lat, lon]}
                      radius={isSelected ? 12 : 8}
                      pathOptions={{
                        color: "#ffffff",
                        weight: isSelected ? 3 : 2,
                        fillColor: isSelected ? "#06372b" : "#2d8a57",
                        fillOpacity: isSelected ? 1 : 0.85,
                      }}
                    >
                      <Popup>
                        <div className="map-popup-card">
                          <strong className="popup-title">
                            {p.panchayat_name} Gram Panchayat
                          </strong>
                          <div className="popup-meta">
                            <span>Block: {p.block_name}</span>
                            <span>District: {p.district_name}</span>
                            <span>LGD Code: {p.gp_code}</span>
                            <span>
                              Coords: {lat.toFixed(4)}°N, {lon.toFixed(4)}°E
                            </span>
                          </div>

                          <div className="popup-forecast-row">
                            <div>
                              <span className="popup-label">Rain (P50):</span>
                              <strong>{p50.toFixed(1)} mm</strong>
                            </div>
                            <div>
                              <span className="popup-label">Uncertainty:</span>
                              <span>
                                {p10.toFixed(1)} – {p90.toFixed(1)} mm
                              </span>
                            </div>
                          </div>

                          <div className="popup-chip-row">
                            <span className={`popup-chip ${chip.type}`}>
                              {chip.icon} {chip.label}
                            </span>
                          </div>

                          {!isSelected && onSelectPanchayat && (
                            <button
                              type="button"
                              className="popup-select-btn"
                              onClick={() => onSelectPanchayat(p)}
                            >
                              📍 Inspect This Panchayat
                            </button>
                          )}
                          {isSelected && (
                            <div className="popup-active-tag">
                              ✓ Currently Active on Dashboard
                            </div>
                          )}
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </MapContainer>
            </MapErrorBoundary>
          </div>

          {/* Map Legend */}
          <div className="map-legend">
            <span>
              <i className="legend-selected"></i>
              Active Panchayat ({data?.panchayat_name || "Selected"})
            </span>
            <span>
              <i className="legend-panchayat"></i>
              Neighboring Panchayats in {blockName}
            </span>
            <span>
              <i className="legend-block"></i>
              Regional Grid Centroid
            </span>
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
