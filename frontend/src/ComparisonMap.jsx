import { Component, useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { fetchBoundaries } from "./services/api";
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
  const [boundariesData, setBoundariesData] = useState(null);
  const [loadingBoundaries, setLoadingBoundaries] = useState(false);

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

  // Fetch boundaries for the active block or panchayat
  useEffect(() => {
    let active = true;

    async function loadBoundaries() {
      setLoadingBoundaries(true);
      try {
        const geojson = await fetchBoundaries({
          block: blockName,
          gpCode: activePanchayat?.gp_code || data?.gp_code,
          panchayatId: currentPanchayatId,
          district: districtName,
        });
        if (active && geojson && Array.isArray(geojson.features)) {
          setBoundariesData(geojson);
        }
      } catch (err) {
        console.warn("Could not load boundaries for spatial map:", err);
      } finally {
        if (active) setLoadingBoundaries(false);
      }
    }

    loadBoundaries();

    return () => {
      active = false;
    };
  }, [blockName, districtName, currentPanchayatId, activePanchayat?.gp_code, data?.gp_code]);

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

  const getFeatureStyle = (feature) => {
    const props = feature.properties || {};
    const featCode = String(props.gp_code || props.GPCODE || "");
    const featId = String(props.panchayat_id || "");

    const isSelected =
      featId === currentPanchayatId ||
      featCode === String(activePanchayat?.gp_code || data?.gp_code || "");

    if (isSelected) {
      return {
        color: "#06372b",
        weight: 3.5,
        opacity: 1,
        fillColor: "#2d8a57",
        fillOpacity: 0.42,
      };
    }

    return {
      color: "#2d8a57",
      weight: 1.8,
      opacity: 0.8,
      fillColor: "#48bb78",
      fillOpacity: 0.12,
      dashArray: "4, 4",
    };
  };

  const onEachFeature = (feature, layer) => {
    const props = feature.properties || {};
    const name = props.panchayat_name || props.GPNAME || "Panchayat";
    const code = props.gp_code || props.GPCODE;
    const block = props.block_name || props.blkname || blockName;
    const district = props.district_name || districtName;
    const featId = props.panchayat_id || (code ? `WB_${code}` : "");

    const isSelected =
      featId === currentPanchayatId ||
      String(code) === String(activePanchayat?.gp_code || data?.gp_code || "");

    // Interactive tooltip
    if (isSelected) {
      layer.bindTooltip(
        `<div class="map-boundary-tooltip active"><strong>📍 ${name}</strong><br/><small>Rain: ${p50.toFixed(1)} mm (${p10.toFixed(1)}–${p90.toFixed(1)} mm)</small></div>`,
        { permanent: true, direction: "center", className: "active-gp-boundary-label" }
      );
    } else {
      layer.bindTooltip(
        `<div class="map-boundary-tooltip"><strong>${name} Gram Panchayat</strong><br/><small>Block: ${block} • LGD: ${code || "—"}</small><br/><span class="boundary-click-cta">📍 Click to Select</span></div>`,
        { sticky: true, className: "neighbor-gp-boundary-label" }
      );
    }

    // Direct click selection: selects this panchayat on the dashboard immediately!
    layer.on({
      mouseover: (e) => {
        const target = e.target;
        target.setStyle({
          weight: isSelected ? 4 : 2.8,
          color: "#06372b",
          fillOpacity: isSelected ? 0.55 : 0.28,
        });
        target.bringToFront();
      },
      mouseout: (e) => {
        const target = e.target;
        target.setStyle(getFeatureStyle(feature));
      },
      click: () => {
        const targetPanchayat = {
          panchayat_id: featId,
          gp_code: Number(code),
          panchayat_name: name,
          block_name: block,
          district_name: district,
          latitude: Number(props.latitude) || activeLat,
          longitude: Number(props.longitude) || activeLon,
        };
        if (onSelectPanchayat) {
          onSelectPanchayat(targetPanchayat);
        }
      },
    });
  };

  return (
    <section className="comparison-section">
      {/* Heading & Meta */}
      <div className="comparison-heading">
        <div>
          <p className="eyebrow">SPATIAL INTELLIGENCE & BOUNDARY DOWN-SCALING</p>
          <h3>Panchayat Boundaries & Regional Comparison</h3>
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
              PANCHAYAT SPATIAL BOUNDARIES ({blockName.toUpperCase()} BLOCK)
            </span>
            <span className="map-status">
              {loadingBoundaries
                ? "LOADING BOUNDARIES..."
                : `${boundariesData?.features?.length || 0} BOUNDARIES ACTIVE`}
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

                {/* Panchayat Administrative Boundaries */}
                {boundariesData && boundariesData.features && (
                  <GeoJSON
                    key={`${currentPanchayatId}-${boundariesData.features.length}`}
                    data={boundariesData}
                    style={getFeatureStyle}
                    onEachFeature={onEachFeature}
                  />
                )}
              </MapContainer>
            </MapErrorBoundary>
          </div>

          {/* Map Legend */}
          <div className="map-legend">
            <span>
              <i className="legend-selected-boundary"></i>
              Selected Panchayat ({data?.panchayat_name || activePanchayat?.panchayat_name || "Active"})
            </span>
            <span>
              <i className="legend-neighbor-boundary"></i>
              Neighboring Boundaries in {blockName} (Click to Select)
            </span>
            <span>
              <i className="legend-block"></i>
              Regional Grid Centroid (~25 km)
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
