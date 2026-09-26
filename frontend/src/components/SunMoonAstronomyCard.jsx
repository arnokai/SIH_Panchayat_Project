export default function SunMoonAstronomyCard({ astronomy, panchayatName = "" }) {
  if (!astronomy) return null;

  const {
    sunrise = "05:27 AM",
    sunset = "05:26 PM",
    solar_noon = "11:26 AM",
    day_length = "12h 0m",
    moon_phase = "Full Moon (Purnima)",
    moon_icon = "🌕",
    moon_illumination_pct = 99.8,
    agricultural_lunar_guidance = "Peak moisture uptake & seed germination vigour; monitor night insect pests",
  } = astronomy;

  return (
    <section className="astronomy-card" aria-label="Sun and Moon Astronomy Tracker">
      <div className="astronomy-header">
        <div className="astronomy-title-block">
          <span className="astronomy-header-icon">☀️🌙</span>
          <div>
            <h3 className="astronomy-title">Solar Arc &amp; Lunar Ephemeris</h3>
            <p className="astronomy-subtitle">
              Astronomical daylight duration, solar noon, and traditional lunar planting cycles for {panchayatName || "Active Panchayat"}
            </p>
          </div>
        </div>
        <div className="daylength-badge">
          <span className="daylength-icon">⏳</span>
          <span>Daylight: <strong>{day_length}</strong></span>
        </div>
      </div>

      <div className="astronomy-dual-layout">
        {/* Left: Solar Arc */}
        <div className="solar-tracker-panel">
          <div className="panel-kicker">SOLAR DAYLIGHT TRACKER</div>
          
          <div className="solar-arc-visual">
            <div className="arc-path"></div>
            <div className="sun-marker noon-marker" title="Solar Noon">
              <span className="sun-dot">☀️</span>
            </div>
          </div>

          <div className="solar-times-grid">
            <div className="solar-time-col">
              <span className="time-label">🌅 SUNRISE</span>
              <strong className="time-val">{sunrise}</strong>
              <small className="time-sub">Dawn Twilight</small>
            </div>

            <div className="solar-time-col">
              <span className="time-label">☀️ SOLAR NOON</span>
              <strong className="time-val">{solar_noon}</strong>
              <small className="time-sub">Peak Solar Elevation</small>
            </div>

            <div className="solar-time-col">
              <span className="time-label">🌇 SUNSET</span>
              <strong className="time-val">{sunset}</strong>
              <small className="time-sub">Dusk Golden Hour</small>
            </div>
          </div>
        </div>

        {/* Right: Lunar Phase & Traditional Agricultural Context */}
        <div className="lunar-tracker-panel">
          <div className="panel-kicker">LUNAR PHASE &amp; AGRI-CYCLE</div>

          <div className="lunar-hero-row">
            <div className="lunar-phase-icon-box">
              <span className="lunar-icon">{moon_icon}</span>
            </div>
            <div>
              <h4 className="lunar-phase-name">{moon_phase}</h4>
              <div className="lunar-illumination-row">
                <span className="illumination-meter-track">
                  <span
                    className="illumination-meter-fill"
                    style={{ width: `${Math.min(100, Math.max(0, moon_illumination_pct))}%` }}
                  ></span>
                </span>
                <span className="illumination-text">
                  <strong>{moon_illumination_pct}%</strong> Illuminated
                </span>
              </div>
            </div>
          </div>

          <div className="lunar-agri-box">
            <span className="agri-icon">🌾</span>
            <div className="agri-text">
              <strong>Traditional Rural Lunar Guidance:</strong> {agricultural_lunar_guidance}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
