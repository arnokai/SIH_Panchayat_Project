import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";


/* =========================================================
   PANCHAYAT LOCATIONS
========================================================= */

const PANCHAYATS = [
  {
    id: "A1",
    name: "ADHATA",
    latitude: 22.876500,
    longitude: 88.530350,
  },
  {
    id: "A2",
    name: "AMDANGA",
    latitude: 22.804947,
    longitude: 88.509614,
  },
  {
    id: "A3",
    name: "BERABERIA",
    latitude: 22.775418,
    longitude: 88.445864,
  },
  {
    id: "A4",
    name: "BODAI",
    latitude: 22.793005,
    longitude: 88.478018,
  },
  {
    id: "A5",
    name: "CHANDIGARH",
    latitude: 22.865638,
    longitude: 88.484222,
  },
  {
    id: "A6",
    name: "MARICHA",
    latitude: 22.915610,
    longitude: 88.526563,
  },
  {
    id: "A7",
    name: "SADHANPUR",
    latitude: 22.836689,
    longitude: 88.504034,
  },
  {
    id: "A8",
    name: "TARABERIA",
    latitude: 22.821180,
    longitude: 88.460015,
  },
];


/* =========================================================
   BLOCK CENTRE
========================================================= */

const BLOCK_CENTER = {
  latitude: 22.836123,
  longitude: 88.492335,
};


/* =========================================================
   MAP VIEW CONTROLLER
========================================================= */

function MapViewController({ selectedId }) {
  const map = useMap();

  const selected = PANCHAYATS.find(
    (panchayat) => panchayat.id === selectedId
  );

  if (selected) {
    map.setView(
      [
        selected.latitude,
        selected.longitude,
      ],
      13,
      {
        animate: true,
      }
    );
  }

  return null;
}


/* =========================================================
   MAIN COMPONENT
========================================================= */

function ComparisonMap({
  forecastDays = [],
  selectedId = "A2",
  selectedDate,
  onDateChange,
}) {
  const selectedDay =
    forecastDays.find(
      (day) => day.date === selectedDate
    ) ||
    forecastDays[0];


  const rainMm =
    selectedDay?.rain_mm?.p50 ?? null;

  const probability =
    selectedDay?.rain_probability ?? null;

  const tmax =
    selectedDay?.tmax_c?.p50 ?? null;

  const tmin =
    selectedDay?.tmin_c ?? null;


  return (
    <section className="comparison-section">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="comparison-heading">

        <div>
          <p className="eyebrow">
            BLOCK → PANCHAYAT
          </p>

          <h3>
            Spatial Forecast Comparison
          </h3>
        </div>

        <div className="comparison-date">
          {selectedDay?.date || "—"}
        </div>

      </div>


      {/* =====================================================
          DATE SELECTOR
      ===================================================== */}

      <div className="comparison-day-selector">

        {forecastDays.map((day) => {

          const active =
            day.date === selectedDay?.date;

          const date = new Date(
            `${day.date}T00:00:00`
          );

          const label =
            date.toLocaleDateString(
              "en-IN",
              {
                weekday: "short",
                day: "numeric",
                month: "short",
              }
            );

          return (
            <button
              key={day.date}
              type="button"
              className={
                active
                  ? "comparison-day-button active"
                  : "comparison-day-button"
              }
              onClick={() =>
                onDateChange?.(day.date)
              }
            >
              {label}
            </button>
          );
        })}

      </div>


      {/* =====================================================
          LAYOUT
      ===================================================== */}

      <div className="comparison-layout">

        {/* ===================================================
            BLOCK FORECAST
        =================================================== */}

        <div className="block-comparison-card">

          <span className="comparison-kicker">
            BLOCK FORECAST
          </span>

          <strong className="block-rain-value">

            {rainMm ?? "—"}

            <span>
              {" "}mm
            </span>

          </strong>

          <p>
            Common coarse forecast currently used
            as the five-day fallback.
          </p>


          <div className="block-mini-stats">

            <div>
              <span>
                RAIN PROB.
              </span>

              <strong>
                {probability !== null
                  ? `${Math.round(
                      probability * 100
                    )}%`
                  : "—"}
              </strong>
            </div>

            <div>
              <span>
                MAX TEMP.
              </span>

              <strong>
                {tmax !== null
                  ? `${tmax}°C`
                  : "—"}
              </strong>
            </div>

            <div>
              <span>
                MIN TEMP.
              </span>

              <strong>
                {tmin !== null
                  ? `${tmin}°C`
                  : "—"}
              </strong>
            </div>

          </div>


          <div className="block-location">

            <span>
              BLOCK CENTRE
            </span>

            <strong>
              {BLOCK_CENTER.latitude.toFixed(4)}
              {", "}
              {BLOCK_CENTER.longitude.toFixed(4)}
            </strong>

          </div>

        </div>


        {/* ===================================================
            REAL LEAFLET MAP
        =================================================== */}

        <div className="map-card">

          <div className="map-title">

            <span>
              PANCHAYAT LOCATIONS
            </span>

            <span className="map-status">
              FALLBACK DATA
            </span>

          </div>


          <div className="leaflet-map-wrapper">

            <MapContainer
              center={[
                BLOCK_CENTER.latitude,
                BLOCK_CENTER.longitude,
              ]}
              zoom={13}
              scrollWheelZoom={true}
              className="leaflet-map"
            >

              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />


              <MapViewController
                selectedId={selectedId}
              />


              {/* =========================================
                  BLOCK CENTRE
              ========================================= */}

              <CircleMarker
                center={[
                  BLOCK_CENTER.latitude,
                  BLOCK_CENTER.longitude,
                ]}
                radius={10}
                pathOptions={{
                  color: "#ffffff",
                  weight: 3,
                  fillColor: "#06372b",
                  fillOpacity: 1,
                }}
              >

                <Popup>

                  <strong>
                    Block Centre
                  </strong>

                  <br />

                  Forecast date:
                  {" "}
                  {selectedDay?.date || "—"}

                  <br />

                  Rainfall:
                  {" "}
                  {rainMm ?? "—"} mm

                  <br />

                  Probability:
                  {" "}
                  {probability !== null
                    ? `${Math.round(
                        probability * 100
                      )}%`
                    : "—"}

                </Popup>

              </CircleMarker>


              {/* =========================================
                  PANCHAYATS
              ========================================= */}

              {PANCHAYATS.map(
                (panchayat) => {

                  const isSelected =
                    panchayat.id ===
                    selectedId;

                  return (
                    <CircleMarker
                      key={panchayat.id}
                      center={[
                        panchayat.latitude,
                        panchayat.longitude,
                      ]}
                      radius={
                        isSelected
                          ? 11
                          : 8
                      }
                      pathOptions={{
                        color: "#ffffff",
                        weight: 2,
                        fillColor:
                          isSelected
                            ? "#082b20"
                            : "#4da36b",
                        fillOpacity: 0.95,
                      }}
                    >

                      <Popup>

                        <strong>
                          {panchayat.name}
                        </strong>

                        <br />

                        Panchayat ID:
                        {" "}
                        {panchayat.id}

                        <br />

                        Latitude:
                        {" "}
                        {panchayat.latitude.toFixed(
                          6
                        )}

                        <br />

                        Longitude:
                        {" "}
                        {panchayat.longitude.toFixed(
                          6
                        )}

                        <br />
                        <br />

                        Forecast:
                        {" "}
                        {rainMm ?? "—"} mm

                        <br />

                        Date:
                        {" "}
                        {selectedDay?.date ||
                          "—"}

                        <br />
                        <br />

                        <small>
                          Common block fallback
                        </small>

                      </Popup>

                    </CircleMarker>
                  );
                }
              )}

            </MapContainer>

          </div>


          {/* =================================================
              LEGEND
          ================================================= */}

          <div className="map-legend">

            <span>
              <i className="legend-block"></i>
              Block centre
            </span>

            <span>
              <i className="legend-panchayat"></i>
              Panchayat
            </span>

            <span>
              <i className="legend-selected"></i>
              Selected Panchayat
            </span>

          </div>

        </div>

      </div>


      {/* =====================================================
          HONEST STATUS
      ===================================================== */}

      <div className="comparison-note">

        <strong>
          Spatial downscaling status:
        </strong>

        {" "}

        Panchayat-specific five-day rainfall
        values are not displayed yet because
        the current multi-day spatial model has
        not been validated. The map shows the
        real Panchayat locations while the
        selected-day forecast remains the common
        block-level fallback.

      </div>

    </section>
  );
}


export default ComparisonMap;