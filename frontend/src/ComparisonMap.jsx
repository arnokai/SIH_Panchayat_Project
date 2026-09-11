import { Component, useEffect, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  Tooltip,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
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
function MapViewController({ center, zoom = 12 }) {
  const map = useMap();
  const prevCenterRef = useRef(null);

  useEffect(() => {
    if (
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
          map.flyTo(center, zoom, { duration: 1.0 });
        } catch (err) {
          console.warn("Leaflet flyTo failed:", err);
        }
      }
    }
  }, [center, zoom, map]);

  return null;
}

function ComparisonMapInner({
  data,
  forecastDays = [],
  selectedDate,
  onDateChange,
  activePanchayat = null,
}) {
  // Target Gram Panchayat Coordinates
  const panchayatLat =
    Number(activePanchayat?.latitude) ||
    Number(data?.panchayat_lat) ||
    Number(data?.coarse_coordinate?.latitude) ||
    22.804947;
  const panchayatLon =
    Number(activePanchayat?.longitude) ||
    Number(data?.panchayat_lon) ||
    Number(data?.coarse_coordinate?.longitude) ||
    88.509614;

  const coarseLat =
    Number(data?.coarse_coordinate?.latitude) || panchayatLat;
  const coarseLon =
    Number(data?.coarse_coordinate?.longitude) || panchayatLon;

  const hasCoarseDifference =
    Math.abs(coarseLat - panchayatLat) > 0.005 ||
    Math.abs(coarseLon - panchayatLon) > 0.005;

  const panchayatName =
    data?.panchayat_name || activePanchayat?.panchayat_name || "Active Panchayat";
  const blockName =
    data?.block_name || activePanchayat?.block_name || "Amdanga";
  const districtName =
    data?.district_name || activePanchayat?.district_name || "North 24 Parganas";

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
              {coarseLat.toFixed(4)}°N, {coarseLon.toFixed(4)}°E
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
            <div className="map-title-left">
              <span>
                PANCHAYAT LOCATION & TERRAIN FOCUS
              </span>
            </div>
            <span className="map-status">
              📍 {blockName}, {districtName}
            </span>
          </div>

          <div className="leaflet-map-wrapper">
            <MapErrorBoundary>
              <MapContainer
                center={[panchayatLat, panchayatLon]}
                zoom={12}
                scrollWheelZoom={false}
                className="leaflet-map"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapViewController
                  center={[panchayatLat, panchayatLon]}
                  zoom={12}
                />

                {/* Regional Coarse Grid Centroid (~25 km) */}
                {hasCoarseDifference && (
                  <CircleMarker
                    center={[coarseLat, coarseLon]}
                    radius={8}
                    pathOptions={{
                      color: "#1e3a8a",
                      fillColor: "#3b82f6",
                      fillOpacity: 0.85,
                      weight: 2,
                    }}
                  >
                    <Tooltip direction="top" offset={[0, -8]}>
                      <strong>Regional Grid Centroid (~25 km)</strong>
                      <br />
                      Baseline Rain: {p50.toFixed(1)} mm
                    </Tooltip>
                    <Popup>
                      <div className="map-popup-card">
                        <h4>Regional Atmospheric Grid</h4>
                        <p><strong>Resolution:</strong> ~25 km coarse ECMWF/GFS</p>
                        <p><strong>Centroid:</strong> {coarseLat.toFixed(4)}°N, {coarseLon.toFixed(4)}°E</p>
                        <p><strong>Regional Baseline:</strong> {p50.toFixed(1)} mm</p>
                      </div>
                    </Popup>
                  </CircleMarker>
                )}

                {/* Micro-terrain radius halo */}
                <CircleMarker
                  center={[panchayatLat, panchayatLon]}
                  radius={20}
                  pathOptions={{
                    color: "#2d8a57",
                    fillColor: "#2d8a57",
                    fillOpacity: 0.15,
                    weight: 1.5,
                    dashArray: "4, 4",
                  }}
                />

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
                      <p><strong>LGD Code:</strong> {activePanchayat?.gp_code || data?.gp_code || "—"}</p>
                      <p><strong>Block:</strong> {blockName} | <strong>District:</strong> {districtName}</p>
                      <p><strong>Coordinates:</strong> {panchayatLat.toFixed(4)}°N, {panchayatLon.toFixed(4)}°E</p>
                      <p><strong>Downscaled Rain:</strong> {p50.toFixed(1)} mm ({p10.toFixed(1)}–{p90.toFixed(1)} mm)</p>
                      {activePanchayat?.elevation_m && (
                        <p><strong>Elevation:</strong> {Math.round(activePanchayat.elevation_m)} m</p>
                      )}
                      {activePanchayat?.soil_type && (
                        <p><strong>Soil:</strong> {activePanchayat.soil_type.replace("_", " ")}</p>
                      )}
                    </div>
                  </Popup>
                </CircleMarker>
              </MapContainer>
            </MapErrorBoundary>
          </div>

          {/* Map Legend */}
          <div className="map-legend">
            <span>
              <i className="legend-selected-pin"></i>
              {panchayatName} (Downscaled Target)
            </span>
            {hasCoarseDifference && (
              <span>
                <i className="legend-coarse-grid"></i>
                Regional Grid Centroid (~25 km)
              </span>
            )}
            <span>
              <i className="legend-radius"></i>
              Local Micro-Terrain Buffer
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
