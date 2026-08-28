import { useEffect, useState } from "react";
import "./App.css";

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

function App() {
  const [selectedId, setSelectedId] = useState("A2");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchForecast() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `http://127.0.0.1:8000/v1/forecast?panchayat_id=${selectedId}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch forecast");
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError("Unable to connect to the forecast server.");
      } finally {
        setLoading(false);
      }
    }

    fetchForecast();
  }, [selectedId]);

  const rainProbability = data
    ? Math.round(data.forecast.rain_probability * 100)
    : 0;

  const priority = data?.advisory?.priority?.toLowerCase() || "low";

  return (
    <div className="app">

      {/* =========================
          HEADER
      ========================= */}
      <header className="header">
        <div className="header-inner">

          <div className="brand-block">
            <h1>TerraMind</h1>
            <p>Panchayat-Level Weather Intelligence</p>
          </div>

          <div className="location">
            AMDANGA BLOCK <span>•</span> NORTH 24 PARGANAS
          </div>

        </div>
      </header>


      <main className="container">

        {/* =========================
            PANCHAYAT SELECTOR
        ========================= */}
        <section className="selector-card">

          <div className="selector-left">

            <label htmlFor="panchayat-select">
              PANCHAYAT
            </label>

            <select
              id="panchayat-select"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              {PANCHAYATS.map((panchayat) => (
                <option
                  key={panchayat.id}
                  value={panchayat.id}
                >
                  {panchayat.name}
                </option>
              ))}
            </select>

          </div>

          <div className="model-status">
            <span className="status-dot"></span>
            <span>V1 MODEL ACTIVE</span>
          </div>

        </section>


        {/* =========================
            LOADING
        ========================= */}
        {loading && (
          <div className="loading">
            <div className="loading-spinner"></div>
            <span>Loading forecast...</span>
          </div>
        )}


        {/* =========================
            ERROR
        ========================= */}
        {error && (
          <div className="error">
            <strong>Forecast unavailable</strong>
            <span>{error}</span>
          </div>
        )}


        {/* =========================
            DASHBOARD
        ========================= */}
        {!loading && !error && data && (
          <div className="dashboard">

            {/* =========================
                FORECAST HEADER
            ========================= */}
            <section className="forecast-heading">

              <div>
                <p className="eyebrow">
                  TODAY'S FORECAST
                </p>

                <h2>
                  {data.panchayat_name}
                </h2>
              </div>

              <div className="forecast-date">
                <span>FORECAST DATE</span>
                <strong>{data.forecast.date}</strong>
              </div>

            </section>


            {/* =========================
                WEATHER METRICS
            ========================= */}
            <section className="forecast-grid">

              {/* RAINFALL */}
              <div className="metric-card">

                <div className="metric-top">
                  <p>RAINFALL</p>
                  <div className="metric-icon rain-icon">↘</div>
                </div>

                <strong className="metric-value">
                  {data.forecast.rain_mm}
                  <span> mm</span>
                </strong>

                <small>
                  Expected rainfall
                </small>

              </div>


              {/* RAIN PROBABILITY */}
              <div className="metric-card">

                <div className="metric-top">
                  <p>RAIN PROBABILITY</p>
                  <div className="metric-icon probability-icon">%</div>
                </div>

                <strong className="metric-value">
                  {rainProbability}
                  <span>%</span>
                </strong>

                <small>
                  Probability of rain
                </small>

                <div className="probability-bar">
                  <div
                    className="probability-fill"
                    style={{
                      width: `${rainProbability}%`,
                    }}
                  ></div>
                </div>

              </div>


              {/* TEMPERATURE */}
              <div className="metric-card">

                <div className="metric-top">
                  <p>MAX TEMPERATURE</p>
                  <div className="metric-icon temp-icon">°</div>
                </div>

                <strong className="metric-value">
                  {data.forecast.tmax_c}
                  <span>°C</span>
                </strong>

                <small>
                  Expected maximum temperature
                </small>

              </div>

            </section>


            {/* =========================
                AGRICULTURAL ADVISORY
            ========================= */}
            <section className={`advisory advisory-${priority}`}>

              <div className="advisory-top">

                <div>
                  <p className="eyebrow">
                    AGRICULTURAL ADVISORY
                  </p>

                  <h3>
                    Action Recommendation
                  </h3>
                </div>

                <span className={`priority priority-${priority}`}>
                  {priority.toUpperCase()}
                </span>

              </div>


              {data.advisory.text_en ? (
                <div className="advisory-content">

                  <p className="advisory-en">
                    {data.advisory.text_en}
                  </p>

                  {data.advisory.text_bn && (
                    <p className="advisory-bn">
                      {data.advisory.text_bn}
                    </p>
                  )}

                </div>
              ) : (
                <div className="advisory-content">

                  <p className="advisory-en">
                    No special agricultural advisory for today.
                  </p>

                  <p className="advisory-note">
                    Continue normal agricultural operations
                    while monitoring local weather conditions.
                  </p>

                </div>
              )}

            </section>


            {/* =========================
                SYSTEM INFORMATION
            ========================= */}
            <section className="info-grid">

              <div className="info-card">
                <span>MODEL VERSION</span>
                <strong>
                  {data.model_version}
                </strong>
              </div>

              <div className="info-card">
                <span>DATA SOURCE</span>
                <strong>
                  Historical Weather + Terrain
                </strong>
              </div>

              <div className="info-card">
                <span>PANCHAYAT ID</span>
                <strong>
                  {data.panchayat_id}
                </strong>
              </div>

            </section>

          </div>
        )}

      </main>


      {/* =========================
          FOOTER
      ========================= */}
      <footer>
        TerraMind <span>•</span> Panchayat Weather Intelligence
        <span>•</span> V1 Prototype
      </footer>

    </div>
  );
}

export default App;