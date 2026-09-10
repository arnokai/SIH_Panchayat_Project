import { useEffect, useState } from "react";
import "./App.css";
import ComparisonMap from "./ComparisonMap";


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
  const [selectedId, setSelectedId] = useState("WB_107001");

  const [selectedCrop, setSelectedCrop] = useState("paddy");

  const [data, setData] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [mapDate, setMapDate] = useState("");

  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [activeStatewideGP, setActiveStatewideGP] = useState(null);

  const PILOT_LGD_MAP = {
    107777: "A1",
    107778: "A2",
    107779: "A3",
    107780: "A4",
    107781: "A5",
    107782: "A6",
    107783: "A7",
    107784: "A8",
  };

  const handleSearchChange = async (val) => {
    setSearchTerm(val);
    if (!val || val.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiBase}/v1/statewide/panchayats?search=${encodeURIComponent(val.trim())}&limit=6`);
      if (res.ok) {
        const json = await res.json();
        setSearchResults(json.panchayats || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectStatewide = (gp) => {
    setSearchTerm(gp.panchayat_name);
    setSearchResults([]);
    if (PILOT_LGD_MAP[gp.gp_code]) {
      setSelectedId(PILOT_LGD_MAP[gp.gp_code]);
      setActiveStatewideGP(null);
    } else {
      setSelectedId(gp.panchayat_id);
      setActiveStatewideGP(gp);
    }
  };


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
          `&lang=en` +
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




        </div>

      </header>


      <main className="container">



{/* ====================================================
            GOOGLE WEATHER HERO
        ==================================================== */}
        {data && data.live_weather && (
          <section className="google-weather-card">
            
            {/* Location Header inside the card */}
            <div className="gw-location">
              <h2>{data.panchayat_name}</h2>
              <p>{(data.block_name || "").toUpperCase()}, {(data.district_name || "").toUpperCase()}</p>
            </div>

            <div className="gw-current">
              <div className="gw-temp-main">
                <img 
                  src={
                    data.live_weather.current.precipitation > 0 || data.live_weather.current.weather_code >= 50
                      ? "https://ssl.gstatic.com/onebox/weather/64/rain.png"
                      : data.live_weather.current.weather_code > 0
                        ? "https://ssl.gstatic.com/onebox/weather/64/partly_cloudy.png"
                        : "https://ssl.gstatic.com/onebox/weather/64/sunny.png"
                  } 
                  alt="weather icon" 
                  className="gw-icon-main"
                />
                <span className="gw-temp">{Math.round(data.live_weather.current.temperature_2m)}</span>
                <span className="gw-unit">°C</span>
              </div>
              
              <div className="gw-details">
                <div className="gw-condition">
                  {data.live_weather.current.precipitation > 0 || data.live_weather.current.weather_code >= 50 ? "Rainy" : data.live_weather.current.weather_code > 0 ? "Partly cloudy" : "Clear"}
                </div>
                <div>Precipitation: {data.live_weather.current.precipitation} mm</div>
                <div>Humidity: {data.live_weather.current.relative_humidity_2m}%</div>
                <div>Wind: {data.live_weather.current.wind_speed_10m} km/h</div>
              </div>
            </div>

            <div className="gw-tabs">
              <button className="gw-tab active">Temperature</button>
              <button className="gw-tab">Precipitation</button>
              <button className="gw-tab">Wind</button>
            </div>
            
            <div className="gw-hourly-slider">
              {data.live_weather.hourly.time.slice(0, 24).map((timeStr, idx) => {
                 const d = new Date(timeStr);
                 const now = new Date();
                 if (d < now && idx !== 0 && now - d > 3600000) return null;
                 
                 const hourCode = data.live_weather.hourly.weather_code[idx];
                 const hourIcon = hourCode >= 50 
                    ? "https://ssl.gstatic.com/onebox/weather/48/rain.png" 
                    : hourCode > 0 
                      ? "https://ssl.gstatic.com/onebox/weather/48/partly_cloudy.png" 
                      : "https://ssl.gstatic.com/onebox/weather/48/sunny.png";
                 
                 return (
                   <div key={timeStr} className="gw-hourly-item">
                     <div className="gw-time">{d.getHours() === now.getHours() ? "Now" : d.getHours() + ":00"}</div>
                     <img src={hourIcon} alt="icon" className="gw-hourly-icon" />
                     <div className="gw-temp-small">{Math.round(data.live_weather.hourly.temperature_2m[idx])}°</div>
                     {data.live_weather.hourly.precipitation_probability[idx] > 0 && (
                       <div className="gw-rain-prob">{data.live_weather.hourly.precipitation_probability[idx]}%</div>
                     )}
                   </div>
                 );
              })}
            </div>
          </section>
        )}
        {/* ====================================================
            PANCHAYAT + CROP SELECTOR
        ==================================================== */}

        <section className="selector-card">





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


          {/* Statewide Search */}

          <div className="selector-left statewide-search-box">

            <label
              htmlFor="statewide-search"
            >
              SEARCH PANCHAYAT (3,339 GPs)
            </label>


            <input
              id="statewide-search"
              type="text"
              placeholder="Search GP e.g. Banchukamari, Falakata..."
              value={searchTerm}
              onChange={(e) =>
                handleSearchChange(
                  e.target.value
                )
              }
              className="statewide-input"
            />

            {searchResults.length > 0 && (
              <ul className="search-dropdown">
                {searchResults.map(
                  (gp) => (
                    <li
                      key={gp.gp_code}
                      onClick={() =>
                        handleSelectStatewide(
                          gp
                        )
                      }
                      className="search-result-item"
                    >
                      <strong>
                        {gp.panchayat_name}
                      </strong>
                      <span>
                        {gp.block_name} • {gp.district_name}
                      </span>
                    </li>
                  )
                )}
              </ul>
            )}

          </div>


          {/* Model status */}

          <div className="model-status">

            <span className="status-dot"></span>


            <div className="model-status-text">
              <span>
                {data?.is_live_dynamic
                  ? "LIVE DYNAMIC WEATHER"
                  : data?.degraded
                  ? "V2 FALLBACK ACTIVE"
                  : "V2 MODEL ACTIVE"}
              </span>

              <small>
                {data?.is_live_dynamic
                  ? "AI Downscaled (Open-Meteo ECMWF/GFS)"
                  : data?.degraded
                  ? "Coarse 5-day forecast"
                  : "AI Downscaled (P10/P50/P90)"}
              </small>
            </div>

          </div>

        </section>

        {activeStatewideGP && (
          <div className="statewide-badge">
            <span className="badge-pin">📍</span>
            <div style={{ flex: 1 }}>
              <strong>{activeStatewideGP.panchayat_name} Gram Panchayat</strong>
              <div style={{ fontSize: "12px", color: "#54786b", marginTop: "2px" }}>
                Block: {activeStatewideGP.block_name} • District: {activeStatewideGP.district_name} • LGD: {activeStatewideGP.gp_code} ({Number(activeStatewideGP.latitude).toFixed(4)}°N, {Number(activeStatewideGP.longitude).toFixed(4)}°E)
              </div>
            </div>
            <button
              className="badge-close"
              onClick={() => {
                setActiveStatewideGP(null);
                setSelectedId("A2");
                setSearchTerm("");
              }}
              style={{
                background: "transparent",
                border: "none",
                fontSize: "16px",
                cursor: "pointer",
                color: "#54786b"
              }}
              title="Close"
            >
              ✕
            </button>
          </div>
        )}


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
                    {data.district_name && (
                      <span style={{ fontSize: "0.5em", fontWeight: 400, color: "#54786b", marginLeft: "10px", display: "inline-block" }}>
                        ({data.block_name ? `${data.block_name} Block, ` : ""}{data.district_name})
                      </span>
                    )}
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
                              ML RAIN PROB.
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

                          <p>
                            {day.advisory?.text_en || day.advisory?.text || "No special advisory."}
                          </p>

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


                  <div className="advisory-top-right">
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

                              {item.text_en ||
                                item.text}

                            </strong>

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