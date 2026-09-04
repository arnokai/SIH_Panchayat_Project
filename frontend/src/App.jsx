import { useEffect, useState } from "react";
import "./App.css";
import ComparisonMap from "./ComparisonMap";


const PANCHAYATS = [
  { id: "A1", name: "ADHATA" },
  { id: "A2", name: "AMDANGA" },
  { id: "A3", name: "BERABERIA" },
  { id: "A4", name: "BODAI" },
  { id: "A5", name: "CHANDIGARH" },
  { id: "A6", name: "MARICHA" },
  { id: "A7", name: "SADHANPUR" },
  { id: "A8", name: "TARABERIA" },
];


const CROPS = [
  { id: "paddy", name: "Paddy" },
  { id: "vegetables", name: "Vegetables" },
];


function formatDate(dateString) {
  const date = new Date(`${dateString}T00:00:00`);

  return date.toLocaleDateString("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}


function getAdvisoryClass(priority) {
  const value = priority?.toLowerCase();

  if (value === "high") return "high";
  if (value === "medium") return "medium";

  return "low";
}


function App() {
  const [selectedId, setSelectedId] = useState("A2");

  const [selectedCrop, setSelectedCrop] = useState("paddy");

  const [data, setData] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [mapDate, setMapDate] = useState("");


  // ==========================================================
  // FETCH FORECAST
  // ==========================================================

  useEffect(() => {
    async function fetchForecast() {
      try {
        setLoading(true);
        setError("");

        const apiBase =
          import.meta.env.VITE_API_BASE_URL ||
          "http://127.0.0.1:8000";

        const url =
          `${apiBase}/v1/forecast` +
          `?panchayat_id=${selectedId}` +
          `&days=5` +
          `&lang=bn` +
          `&crop=${encodeURIComponent(selectedCrop)}`;


        const response = await fetch(url);


        if (!response.ok) {
          throw new Error(
            "Failed to fetch forecast"
          );
        }


        const result = await response.json();


        setMapDate(
          result.forecast?.[0]?.date || ""
        );


        setData(result);

      } catch (err) {
        console.error(err);

        setError(
          "Unable to connect to the forecast server."
        );

      } finally {
        setLoading(false);
      }
    }


    fetchForecast();

  }, [selectedId, selectedCrop]);


  // ==========================================================
  // DERIVED DATA
  // ==========================================================

  const forecastDays =
    data?.forecast || [];


  const activeAdvisories =
    data?.advisories?.filter(
      (item) =>
        item?.priority?.toLowerCase() === "high"
    ) || [];


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="app">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="header">

        <div className="header-inner">

          <div className="brand-block">

            <h1>
              TerraMind
            </h1>

            <p>
              Panchayat-Level Weather Intelligence
            </p>

          </div>


          <div className="location">

            AMDANGA BLOCK
            <span>•</span>
            NORTH 24 PARGANAS

          </div>

        </div>

      </header>


      <main className="container">


        {/* ====================================================
            PANCHAYAT + CROP SELECTOR
        ==================================================== */}

        <section className="selector-card">


          {/* Panchayat */}

          <div className="selector-left">

            <label
              htmlFor="panchayat-select"
            >
              PANCHAYAT
            </label>


            <select
              id="panchayat-select"
              value={selectedId}
              onChange={(e) =>
                setSelectedId(
                  e.target.value
                )
              }
            >

              {PANCHAYATS.map(
                (panchayat) => (

                  <option
                    key={panchayat.id}
                    value={panchayat.id}
                  >
                    {panchayat.name}
                  </option>

                )
              )}

            </select>

          </div>


          {/* Crop */}

          <div className="selector-left">

            <label
              htmlFor="crop-select"
            >
              CROP
            </label>


            <select
              id="crop-select"
              value={selectedCrop}
              onChange={(e) =>
                setSelectedCrop(
                  e.target.value
                )
              }
            >

              {CROPS.map(
                (crop) => (

                  <option
                    key={crop.id}
                    value={crop.id}
                  >
                    {crop.name}
                  </option>

                )
              )}

            </select>

          </div>


          {/* Model status */}

          <div className="model-status">

            <span className="status-dot"></span>


            <div className="model-status-text">

              <span>
                {data?.degraded
                  ? "V2 FALLBACK ACTIVE"
                  : "V2 MODEL ACTIVE"}
              </span>


              {data?.degraded && (
                <small>
                  Coarse 5-day forecast
                </small>
              )}

            </div>

          </div>

        </section>


        {/* ====================================================
            LOADING
        ==================================================== */}

        {loading && (

          <div className="loading">

            <div className="loading-spinner"></div>

            <span>
              Loading 5-day forecast...
            </span>

          </div>

        )}


        {/* ====================================================
            ERROR
        ==================================================== */}

        {error && (

          <div className="error">

            <strong>
              Forecast unavailable
            </strong>

            <span>
              {error}
            </span>

          </div>

        )}


        {/* ====================================================
            DASHBOARD
        ==================================================== */}

        {!loading &&
          !error &&
          data && (

            <div className="dashboard">


              {/* ==============================================
                  FORECAST HEADER
              ============================================== */}

              <section className="forecast-heading">

                <div>

                  <p className="eyebrow">
                    NEXT 5 DAYS
                  </p>


                  <h2>
                    {data.panchayat_name}
                  </h2>

                </div>


                <div className="forecast-meta">

                  <span>
                    ISSUED
                  </span>


                  <strong>

                    {data.issued_at
                      ? new Date(
                          data.issued_at
                        ).toLocaleString(
                          "en-IN",
                          {
                            dateStyle:
                              "medium",

                            timeStyle:
                              "short",
                          }
                        )
                      : "—"}

                  </strong>

                </div>

              </section>


              {/* ==============================================
                  CROP INFORMATION
              ============================================== */}

              <section className="degraded-banner">

                <strong>
                  Selected crop:{" "}
                  {CROPS.find(
                    (crop) =>
                      crop.id === selectedCrop
                  )?.name ||
                    selectedCrop}
                </strong>

                <span>
                  Crop-aware advisory rules are being
                  evaluated for the selected crop.
                </span>

              </section>


              {/* ==============================================
                  DEGRADED NOTICE
              ============================================== */}

              {data.degraded && (

                <section className="degraded-banner">

                  <strong>
                    Prototype forecast mode
                  </strong>


                  <span>
                    {data.degraded_reason}
                  </span>

                </section>

              )}


              {/* ==============================================
                  5-DAY FORECAST
              ============================================== */}

              <section className="five-day-grid">

                {forecastDays.map(
                  (day) => {

                    const priority =
                      getAdvisoryClass(
                        day.advisory?.priority
                      );


                    const probability =
                      Math.round(
                        (day.rain_probability || 0) *
                        100
                      );


                    return (

                      <article
                        className="day-card"
                        key={day.date}
                      >


                        {/* Day header */}

                        <div className="day-card-header">

                          <div>

                            <p className="day-name">
                              {formatDate(
                                day.date
                              )}
                            </p>


                            <span className="day-date">
                              {day.date}
                            </span>

                          </div>


                          <div className="day-rain-symbol">

                            {day.rain_mm?.p50 > 0
                              ? "↘"
                              : "—"}

                          </div>

                        </div>


                        {/* Rain */}

                        <div className="day-main-weather">

                          <div className="rain-value">

                            <strong>
                              {day.rain_mm?.p50 ??
                                "—"}
                            </strong>

                            <span>
                              mm
                            </span>

                          </div>


                          <p>
                            Expected rainfall
                          </p>

                        </div>


                        {/* Statistics */}

                        <div className="day-stats">


                          <div>

                            <span>
                              RAIN PROB.
                            </span>

                            <strong>
                              {probability}%
                            </strong>

                          </div>


                          <div>

                            <span>
                              TEMP.
                            </span>

                            <strong>
                              {day.tmax_c?.p50 ??
                                "—"}°C
                            </strong>

                          </div>


                          <div>

                            <span>
                              MIN.
                            </span>

                            <strong>
                              {day.tmin_c ??
                                "—"}°C
                            </strong>

                          </div>

                        </div>


                        {/* Probability */}

                        <div className="probability-bar">

                          <div
                            className="probability-fill"
                            style={{
                              width:
                                `${probability}%`,
                            }}
                          ></div>

                        </div>


                        {/* Advisory */}

                        <div
                          className={
                            `day-advisory ` +
                            `day-advisory-${priority}`
                          }
                        >

                          <span className="day-advisory-label">
                            ADVISORY
                          </span>


                          {day.advisory?.text_bn ? (

                            <p>
                              {day.advisory.text_bn}
                            </p>

                          ) : day.advisory?.text_en ? (

                            <p>
                              {day.advisory.text_en}
                            </p>

                          ) : (

                            <p>
                              No special advisory.
                            </p>

                          )}

                        </div>

                      </article>

                    );

                  }
                )}

              </section>


              {/* ==============================================
                  MAP
              ============================================== */}

              <ComparisonMap
                forecastDays={
                  forecastDays
                }

                selectedId={
                  selectedId
                }

                selectedDate={
                  mapDate
                }

                onDateChange={
                  setMapDate
                }
              />


              {/* ==============================================
                  AGRICULTURAL ADVISORY
              ============================================== */}

              <section className="advisory">


                <div className="advisory-top">

                  <div>

                    <p className="eyebrow">
                      AGRICULTURAL ADVISORY
                    </p>


                    <h3>
                      Action Recommendation
                    </h3>

                  </div>


                  <span
                    className={
                      `priority priority-${
                        activeAdvisories.length > 0
                          ? "high"
                          : "low"
                      }`
                    }
                  >

                    {activeAdvisories.length > 0
                      ? "ATTENTION"
                      : "LOW"}

                  </span>

                </div>


                {data.advisories?.length > 0 ? (

                  <div className="advisory-list">

                    {data.advisories.map(
                      (item) => (

                        <div
                          className={
                            `advisory-item ` +
                            `advisory-item-${getAdvisoryClass(
                              item.priority
                            )}`
                          }

                          key={
                            `${item.date}-${item.rule_id}`
                          }
                        >

                          <div className="advisory-item-date">

                            {formatDate(
                              item.date
                            )}

                          </div>


                          <div className="advisory-item-body">

                            <strong>

                              {item.text_bn ||
                                item.text_en}

                            </strong>


                            <small>
                              {item.text_en}
                            </small>

                          </div>

                        </div>

                      )
                    )}

                  </div>

                ) : (

                  <div className="advisory-content">

                    <p className="advisory-en">
                      No special agricultural advisory
                      for the next five days.
                    </p>


                    <p className="advisory-note">
                      Continue normal agricultural
                      operations while monitoring local
                      weather conditions.
                    </p>

                  </div>

                )}

              </section>


              {/* ==============================================
                  SYSTEM INFORMATION
              ============================================== */}

              <section className="info-grid">


                <div className="info-card">

                  <span>
                    MODEL VERSION
                  </span>

                  <strong>
                    {data.model_version}
                  </strong>

                </div>


                <div className="info-card">

                  <span>
                    RAINFALL MODEL
                  </span>

                  <strong>
                    {data.rainfall_model}
                  </strong>

                </div>


                <div className="info-card">

                  <span>
                    DATA SOURCE
                  </span>

                  <strong>
                    {data.source}
                  </strong>

                </div>


                <div className="info-card">

                  <span>
                    PANCHAYAT ID
                  </span>

                  <strong>
                    {data.panchayat_id}
                  </strong>

                </div>


                <div className="info-card">

                  <span>
                    CROP
                  </span>

                  <strong>
                    {data.crop}
                  </strong>

                </div>


                <div className="info-card">

                  <span>
                    BLOCK LATITUDE
                  </span>

                  <strong>
                    {data.coarse_coordinate?.latitude}
                  </strong>

                </div>


                <div className="info-card">

                  <span>
                    BLOCK LONGITUDE
                  </span>

                  <strong>
                    {data.coarse_coordinate?.longitude}
                  </strong>

                </div>


              </section>

            </div>

          )}

      </main>


      {/* ======================================================
          FOOTER
      ====================================================== */}

      <footer>

        TerraMind
        <span>•</span>
        Panchayat Weather Intelligence
        <span>•</span>
        V2 Prototype

      </footer>

    </div>
  );
}


export default App;