import { useState, useEffect } from "react";

const CROP_ICONS = {
  paddy: "🌾",
  potato: "🥔",
  mustard: "🌼",
  jute: "🌿",
  vegetables: "🥬",
};

const REQUIRED_CROP_INSTITUTES = {
  paddy: "ICAR-NRRI (National Rice Research Institute) & BCKV Agromet Field Unit",
  potato: "ICAR-CPRI (Central Potato Research Institute) & BCKV Mohanpur",
  mustard: "ICAR-DRMR (Directorate of Rapeseed-Mustard Research) & District KVKs",
  jute: "ICAR-CRIJAF (Central Research Institute for Jute and Allied Fibres, Barrackpore)",
  vegetables: "ICAR-IIHR (Indian Institute of Horticultural Research) & Dept. of Agriculture, WB",
};

export default function CropAdvisorySuite({
  crop = "paddy",
  panchayatId = "WB_107778",
  panchayatName = "Amdanga",
  forecastData = null,
}) {
  const [activeTab, setActiveTab] = useState("doctor"); // "pop", "doctor", "fertilizer", "spray", "water", "mandi"
  const [dossier, setDossier] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fertilizer calculator state
  const [fieldSize, setFieldSize] = useState(1.0);
  const [fieldUnit, setFieldUnit] = useState("acre"); // "acre", "bigha", "hectare"

  // Disease doctor symptom filter
  const [selectedSymptom, setSelectedSymptom] = useState(null);

  // Audio voice synthesis
  const [isSpeaking, setIsSpeaking] = useState(false);

  const cleanCrop = (crop || "paddy").toLowerCase();
  const cropIcon = CROP_ICONS[cleanCrop] || "🌱";

  // Fetch full advisory dossier from backend API
  useEffect(() => {
    let isMounted = true;
    const fetchDossier = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          crop: cleanCrop,
          panchayat_id: panchayatId,
          field_size: fieldSize.toString(),
          unit: fieldUnit,
        });
        const res = await fetch(`/v1/crops/advisory-dossier?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`Failed to load crop advisory dossier (${res.status})`);
        }
        const data = await res.json();
        if (isMounted) {
          setDossier(data);
          setSelectedSymptom(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || "Failed to load crop advisory dossier");
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDossier();
    return () => {
      isMounted = false;
    };
  }, [cleanCrop, panchayatId, fieldSize, fieldUnit]);

  // Audio speech briefing
  const handleSpeakBriefing = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Speech synthesis is not supported on this device.");
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    let textToSpeak = `TerraMind agricultural advisory dossier for ${cleanCrop.toUpperCase()} in ${panchayatName}. `;
    if (dossier?.spray_advisor) {
      textToSpeak += `Agrochemical spray status is ${dossier.spray_advisor.status}. ${dossier.spray_advisor.advisory_reasons[0] || ""} `;
    }
    if (dossier?.water_irrigation_budget) {
      textToSpeak += `Water balance: ${dossier.water_irrigation_budget.action_recommendation} `;
    }
    if (dossier?.fertilizer_calculator?.leaching_risk) {
      textToSpeak += "High rain alert: postpone urea application to avoid fertilizer runoff. ";
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = "en-IN";
    utterance.rate = 0.92;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  // WhatsApp sharing
  const handleShareWhatsApp = () => {
    if (!dossier) return;
    const lines = [
      `🌾 *TerraMind Crop Advisory Suite — ${dossier.crop.toUpperCase()}* 🌾`,
      `📍 *Panchayat:* ${panchayatName} (${panchayatId})`,
      `🗓️ *Growth Phase:* ${dossier.phenology_summary?.current_stage?.toUpperCase() || "Active"}`,
      `🎯 *Spray Suitability:* ${dossier.spray_advisor?.status?.toUpperCase()} (Score: ${dossier.spray_advisor?.score_pct}%)`,
      `💧 *Irrigation Need:* ${dossier.water_irrigation_budget?.net_irrigation_requirement_mm} mm (${dossier.water_irrigation_budget?.irrigation_status})`,
      `🧪 *Fertilizer for ${dossier.fertilizer_calculator?.display_area}:* Urea: ${dossier.fertilizer_calculator?.commercial_fertilizers?.[0]?.quantity_kg}kg, DAP: ${dossier.fertilizer_calculator?.commercial_fertilizers?.[1]?.quantity_kg}kg`,
      dossier.fertilizer_calculator?.leaching_risk ? `⚠️ *Alert:* ${dossier.fertilizer_calculator?.leaching_alert}` : null,
      `🏛️ *Source:* ICAR & BCKV Agromet Field Units`,
      `🔗 _TerraMind Panchayat Agro-Advisory Intelligence_`,
    ]
      .filter(Boolean)
      .join("\n");

    const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(lines)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  // Extract all unique symptom tags from diseases
  const allSymptoms = Array.from(
    new Set((dossier?.pest_and_disease_doctor || []).flatMap((d) => d.visual_tags || []))
  );

  // Filter diseases by selected symptom tag
  const filteredDiseases = (dossier?.pest_and_disease_doctor || []).filter((d) => {
    if (!selectedSymptom) return true;
    return (d.visual_tags || []).includes(selectedSymptom);
  });

  return (
    <section className="crop-advisory-suite">
      {/* Header Bar */}
      <div className="suite-header">
        <div className="suite-title-block">
          <div className="crop-icon-badge">{cropIcon}</div>
          <div>
            <div className="suite-badge-row">
              <span className="suite-live-badge">⚡ Authoritative Crop Dossier</span>
              <span className="suite-crop-tag">{cleanCrop.toUpperCase()}</span>
              {dossier?.phenology_summary?.current_stage && (
                <span className="suite-stage-tag">
                  Phase: {dossier.phenology_summary.current_stage.toUpperCase()}
                </span>
              )}
              <span className="suite-source-pill" title={`Mandatory Research Institute: ${REQUIRED_CROP_INSTITUTES[cleanCrop] || "ICAR"}`}>
                🏛️ Source: {REQUIRED_CROP_INSTITUTES[cleanCrop] || "ICAR & IMD Agromet"}
              </span>
            </div>
            <h3 className="suite-main-title">
              {cropIcon} {cleanCrop.toUpperCase()} Crop Advisory & Farm Management Suite
            </h3>
            <p className="suite-sub-title">
              Precision agronomical decision support grounded in ICAR, BCKV, and IMD Agromet standards for {panchayatName}.
            </p>
          </div>
        </div>

        <div className="suite-header-actions">
          <button
            type="button"
            className={`suite-btn suite-btn-voice ${isSpeaking ? "active" : ""}`}
            onClick={handleSpeakBriefing}
            title="Listen to audio briefing in English"
          >
            {isSpeaking ? "⏹ Stop Audio" : "🔊 Audio Briefing"}
          </button>
          <button
            type="button"
            className="suite-btn suite-btn-share"
            onClick={handleShareWhatsApp}
            title="Share advisory dossier on WhatsApp"
          >
            💬 Share Dossier
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="suite-tabs">
        <button
          type="button"
          className={`suite-tab-btn ${activeTab === "doctor" ? "active" : ""}`}
          onClick={() => setActiveTab("doctor")}
        >
          🩺 Disease Doctor
        </button>
        <button
          type="button"
          className={`suite-tab-btn ${activeTab === "pop" ? "active" : ""}`}
          onClick={() => setActiveTab("pop")}
        >
          📋 Package of Practices
        </button>
        <button
          type="button"
          className={`suite-tab-btn ${activeTab === "fertilizer" ? "active" : ""}`}
          onClick={() => setActiveTab("fertilizer")}
        >
          🧪 Fertilizer Calculator
        </button>
        <button
          type="button"
          className={`suite-tab-btn ${activeTab === "spray" ? "active" : ""}`}
          onClick={() => setActiveTab("spray")}
        >
          🎯 Spray Advisor
        </button>
        <button
          type="button"
          className={`suite-tab-btn ${activeTab === "water" ? "active" : ""}`}
          onClick={() => setActiveTab("water")}
        >
          💧 Irrigation Budget
        </button>
        <button
          type="button"
          className={`suite-tab-btn ${activeTab === "mandi" ? "active" : ""}`}
          onClick={() => setActiveTab("mandi")}
        >
          📈 Mandi Prices
        </button>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="suite-loading-state">
          <div className="suite-spinner"></div>
          <span>Computing crop phenology, NPK splits, and FAO-56 evapotranspiration...</span>
        </div>
      )}

      {error && (
        <div className="suite-error-banner">
          ⚠️ <strong>Notice:</strong> {error}
        </div>
      )}

      {dossier && !loading && (
        <div className="suite-tab-content">
          {/* ========================================================= */}
          {/* TAB 1: PEST & DISEASE DOCTOR */}
          {/* ========================================================= */}
          {activeTab === "doctor" && (
            <div className="doctor-panel">
              <div className="doctor-filter-bar">
                <span className="filter-label">🔍 Filter by Visible Field Symptoms:</span>
                <button
                  type="button"
                  className={`symptom-chip ${selectedSymptom === null ? "active" : ""}`}
                  onClick={() => setSelectedSymptom(null)}
                >
                  All Diseases ({dossier.pest_and_disease_doctor?.length || 0})
                </button>
                {allSymptoms.map((symp) => (
                  <button
                    key={symp}
                    type="button"
                    className={`symptom-chip ${selectedSymptom === symp ? "active" : ""}`}
                    onClick={() => setSelectedSymptom(selectedSymptom === symp ? null : symp)}
                  >
                    {symp}
                  </button>
                ))}
              </div>

              <div className="disease-cards-grid">
                {filteredDiseases.map((dis) => (
                  <div key={dis.id} className="disease-card">
                    <div className="disease-card-header">
                      <div>
                        <span className={`severity-badge ${dis.severity?.toLowerCase()}`}>
                          {dis.severity} Severity
                        </span>
                        <span className="disease-type">{dis.type}</span>
                        <h4 className="disease-name">{dis.name}</h4>
                      </div>
                    </div>

                    <div className="disease-body">
                      <div className="disease-section">
                        <strong className="section-label">Visible Field Symptoms:</strong>
                        <ul className="symptom-list">
                          {(dis.symptoms || []).map((s, idx) => (
                            <li key={idx}>{s}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="disease-weather-box">
                        <span className="weather-icon-badge">🌦️</span>
                        <div>
                          <strong>Weather Triggers:</strong>
                          <p>{dis.weather_triggers}</p>
                        </div>
                      </div>

                      <div className="disease-control-grid">
                        <div className="control-box chemical">
                          <div className="control-header">
                            <span>🧪 Chemical Prescription</span>
                            <span className="phi-badge">PHI: {dis.chemical_control?.phi_days} Days</span>
                          </div>
                          <div className="control-content">
                            <p><strong>Active Formulation:</strong> {dis.chemical_control?.active_ingredient}</p>
                            <p><strong>Dilution:</strong> {dis.chemical_control?.dilution_per_liter}</p>
                            <p><strong>Acre Dosage:</strong> {dis.chemical_control?.acre_dosage}</p>
                          </div>
                        </div>

                        <div className="control-box biological">
                          <div className="control-header">
                            <span>🌿 Bio-Control & Organic</span>
                          </div>
                          <div className="control-content">
                            <p>{dis.biological_control}</p>
                            <p className="cultural-tip">
                              <strong>Cultural Prevention:</strong> {dis.cultural_prevention}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="disease-footer">
                        <span className="source-citation">🏛️ Authority: {dis.source}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 2: STAGE-WISE PACKAGE OF PRACTICES (POP) */}
          {/* ========================================================= */}
          {activeTab === "pop" && (
            <div className="pop-panel">
              <div className="pop-header-banner">
                <div>
                  <h4>Standard Package of Practices (POP) — {cleanCrop.toUpperCase()}</h4>
                  <p>Comprehensive cultural operations calibrated by State Agricultural University (BCKV) and ICAR.</p>
                </div>
                {dossier.phenology_summary && (
                  <div className="gdd-summary-chip">
                    <span>🌡️ Accumulated GDD: <strong>{dossier.phenology_summary.accumulated_gdd}</strong></span>
                    <span>T-Base: <strong>{dossier.phenology_summary.t_base_c}°C</strong></span>
                  </div>
                )}
              </div>

              <div className="pop-timeline">
                {(dossier.package_of_practices || []).map((stage, idx) => {
                  const isActive =
                    dossier.phenology_summary?.current_stage &&
                    stage.stage_id?.toLowerCase().includes(dossier.phenology_summary.current_stage.toLowerCase());

                  return (
                    <div key={stage.stage_id} className={`pop-step-card ${isActive ? "active-stage" : ""}`}>
                      <div className="pop-step-indicator">
                        <div className="step-circle">{idx + 1}</div>
                        {isActive && <span className="active-pulse-badge">Active Phase</span>}
                      </div>

                      <div className="pop-step-content">
                        <div className="pop-step-title-row">
                          <h4 className="pop-step-title">{stage.stage_name}</h4>
                          <div className="pop-step-meta">
                            <span className="duration-tag">⏱️ {stage.duration_days}</span>
                            <span className="gdd-tag">🌡️ {stage.ideal_gdd}</span>
                          </div>
                        </div>

                        <div className="pop-operations-block">
                          <strong>Essential Operations:</strong>
                          <ul>
                            {(stage.key_operations || []).map((op, oIdx) => (
                              <li key={oIdx}>{op}</li>
                            ))}
                          </ul>
                        </div>

                        <div className="pop-subgrid">
                          <div className="pop-subcell water">
                            <strong>💧 Water Management:</strong>
                            <p>{stage.water_management}</p>
                          </div>
                          <div className="pop-subcell nutrient">
                            <strong>🧪 Fertilizer Timing:</strong>
                            <p>{stage.nutrient_advice}</p>
                          </div>
                          <div className="pop-subcell scouting">
                            <strong>🔍 Pest Surveillance:</strong>
                            <p>{stage.pest_scouting}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 3: SMART FERTILIZER & NPK CALCULATOR */}
          {/* ========================================================= */}
          {activeTab === "fertilizer" && dossier.fertilizer_calculator && (
            <div className="fertilizer-panel">
              {/* Field Size Controls */}
              <div className="fert-controls-card">
                <div className="fert-input-group">
                  <label htmlFor="field-size-input">Enter Agricultural Field Size:</label>
                  <div className="fert-input-row">
                    <input
                      id="field-size-input"
                      type="number"
                      step="0.5"
                      min="0.1"
                      max="500"
                      value={fieldSize}
                      onChange={(e) => setFieldSize(Math.max(0.1, parseFloat(e.target.value) || 1.0))}
                      className="fert-number-input"
                    />
                    <select
                      value={fieldUnit}
                      onChange={(e) => setFieldUnit(e.target.value)}
                      className="fert-unit-select"
                    >
                      <option value="acre">Acres</option>
                      <option value="bigha">Bighas (WB Standard: 1 Acre = 3 Bighas)</option>
                      <option value="hectare">Hectares</option>
                    </select>
                  </div>
                </div>

                <div className="quick-size-buttons">
                  <span className="quick-label">Quick Select:</span>
                  {[
                    { label: "1 Bigha", size: 1, unit: "bigha" },
                    { label: "3 Bigha (1 Acre)", size: 1, unit: "acre" },
                    { label: "5 Bigha", size: 5, unit: "bigha" },
                    { label: "2 Acres", size: 2, unit: "acre" },
                  ].map((btn, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className={`quick-pill ${fieldSize === btn.size && fieldUnit === btn.unit ? "active" : ""}`}
                      onClick={() => {
                        setFieldSize(btn.size);
                        setFieldUnit(btn.unit);
                      }}
                    >
                      {btn.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Leaching Risk Warning */}
              {dossier.fertilizer_calculator.leaching_risk ? (
                <div className="leaching-warning-banner active-danger">
                  <span className="alert-icon">⚠️</span>
                  <div>
                    <strong>Weather Alert: Postpone Nitrogen Top Dressing</strong>
                    <p>{dossier.fertilizer_calculator.leaching_alert}</p>
                  </div>
                </div>
              ) : (
                <div className="leaching-warning-banner safe">
                  <span className="alert-icon">✓</span>
                  <div>
                    <strong>Favorable Application Window</strong>
                    <p>{dossier.fertilizer_calculator.leaching_alert}</p>
                  </div>
                </div>
              )}

              {/* Commercial Fertilizer Bags Grid */}
              <div className="fert-cards-grid">
                {(dossier.fertilizer_calculator.commercial_fertilizers || []).map((fert, idx) => (
                  <div key={idx} className="fert-bag-card">
                    <div className="fert-bag-badge" style={{ backgroundColor: fert.color }}>
                      {fert.name.split(" ")[0]}
                    </div>
                    <h4 className="fert-name">{fert.name}</h4>
                    <div className="fert-qty-row">
                      <span className="fert-total-kg">{fert.quantity_kg} kg</span>
                      <span className="fert-bag-count">≈ <strong>{fert.bags_approx}</strong> bags ({fert.bag_spec})</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Split Application Schedule */}
              <div className="split-schedule-card">
                <h4 className="card-subheading">📅 Split Dosage Application Schedule</h4>
                <div className="table-responsive">
                  <table className="split-table">
                    <thead>
                      <tr>
                        <th>Application Timing</th>
                        <th>Urea (kg)</th>
                        <th>DAP (kg)</th>
                        <th>MOP (kg)</th>
                        <th>Cultural Instructions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(dossier.fertilizer_calculator.split_schedule || []).map((split, sIdx) => (
                        <tr key={sIdx}>
                          <td className="timing-cell"><strong>{split.timing}</strong></td>
                          <td className="qty-cell">{split.urea_kg} kg</td>
                          <td className="qty-cell">{split.dap_kg} kg</td>
                          <td className="qty-cell">{split.mop_kg} kg</td>
                          <td className="notes-cell">{split.notes}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Micronutrients Box */}
              {dossier.fertilizer_calculator.micronutrients?.length > 0 && (
                <div className="micronutrient-card">
                  <h4 className="card-subheading">🌿 Critical Micronutrients Required</h4>
                  <div className="micro-grid">
                    {dossier.fertilizer_calculator.micronutrients.map((micro, mIdx) => (
                      <div key={mIdx} className="micro-item">
                        <strong>{micro.name}</strong>
                        <span className="micro-dose">Dose: {micro.dosage}</span>
                        <p className="micro-app">{micro.application}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 4: AGROCHEMICAL SPRAY ADVISOR */}
          {/* ========================================================= */}
          {activeTab === "spray" && dossier.spray_advisor && (
            <div className="spray-panel">
              {/* Spray Status Hero */}
              <div
                className="spray-status-hero"
                style={{ borderColor: dossier.spray_advisor.badge_color }}
              >
                <div className="spray-score-circle" style={{ borderColor: dossier.spray_advisor.badge_color }}>
                  <span className="score-val">{dossier.spray_advisor.score_pct}%</span>
                  <span className="score-lbl">Spray Suitability</span>
                </div>
                <div className="spray-summary-text">
                  <span
                    className="spray-status-pill"
                    style={{ backgroundColor: dossier.spray_advisor.badge_color }}
                  >
                    Status: {dossier.spray_advisor.status.toUpperCase()}
                  </span>
                  <h4>Agrochemical Spray Window Rating</h4>
                  <ul className="spray-reasons-list">
                    {(dossier.spray_advisor.advisory_reasons || []).map((reason, idx) => (
                      <li key={idx}>{reason}</li>
                    ))}
                  </ul>
                  <div className="best-window-callout">
                    ⏱️ <strong>Recommended Spray Hours:</strong> {dossier.spray_advisor.best_spray_window_today}
                  </div>
                </div>
              </div>

              {/* Physical Parameters Meter */}
              <div className="spray-metrics-row">
                <div className="spray-metric-card">
                  <span className="metric-title">Delta-T (Evaporation Index)</span>
                  <div className="metric-val">{dossier.spray_advisor.delta_t_c}°C</div>
                  <span className="metric-range">Optimal: {dossier.spray_advisor.optimal_delta_t_range}</span>
                  <p className="metric-desc">Delta-T measures droplet evaporation rate. Too high causes spray drift; too low delays drying.</p>
                </div>

                <div className="spray-metric-card">
                  <span className="metric-title">Surface Wind Speed</span>
                  <div className="metric-val">{dossier.spray_advisor.wind_speed_kmh} km/h</div>
                  <span className="metric-range">Optimal: {dossier.spray_advisor.optimal_wind_range}</span>
                  <p className="metric-desc">Wind above 15 km/h causes chemical drift; wind below 3 km/h risks surface inversion.</p>
                </div>

                <div className="spray-metric-card">
                  <span className="metric-title">Rainfastness Lead Time</span>
                  <div className="metric-val">≥ {dossier.spray_advisor.rainfast_window_hours} Hours</div>
                  <span className="metric-range">Rain-free buffer needed</span>
                  <p className="metric-desc">Systemic pesticides require 3-4 rainless hours for cuticular leaf penetration.</p>
                </div>
              </div>

              {/* Tank-Mix Compatibility Matrix */}
              <div className="tank-mix-card">
                <div className="tank-mix-header">
                  <div>
                    <h4 className="card-subheading">🧪 Chemical Tank-Mix Compatibility Matrix</h4>
                    <p className="card-desc">Safety guidelines for mixing fungicides, insecticides, and foliar nutrients in a single spray tank.</p>
                  </div>
                  <span className="wales-pill">WALES Protocol Compliant</span>
                </div>

                <div className="wales-banner">
                  <strong>Tank Mixing Order (WALES Protocol):</strong>
                  <span>1. WP/WDG powders ➔ 2. Agitate ➔ 3. Liquid SC/SL ➔ 4. EC concentrates ➔ 5. Stickers</span>
                </div>

                <div className="mix-table-wrap">
                  <table className="mix-table">
                    <thead>
                      <tr>
                        <th>Tank Combination</th>
                        <th>Compatibility Verdict</th>
                        <th>Agronomic Advice</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(dossier.spray_advisor.tank_mix_matrix || []).map((item, idx) => (
                        <tr key={idx}>
                          <td><strong>{item.mix}</strong></td>
                          <td>
                            <span className={`compat-pill ${item.compatibility.toLowerCase()}`}>
                              {item.status_icon} {item.compatibility}
                            </span>
                          </td>
                          <td>{item.note}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 5: CROP WATER & IRRIGATION BUDGET */}
          {/* ========================================================= */}
          {activeTab === "water" && dossier.water_irrigation_budget && (
            <div className="water-panel">
              <div
                className="water-status-hero"
                style={{ borderColor: dossier.water_irrigation_budget.badge_color }}
              >
                <div className="water-summary-col">
                  <span
                    className="water-status-pill"
                    style={{ backgroundColor: dossier.water_irrigation_budget.badge_color }}
                  >
                    {dossier.water_irrigation_budget.irrigation_status}
                  </span>
                  <h4>FAO-56 Crop Evapotranspiration & Water Balance</h4>
                  <p className="water-action-text">{dossier.water_irrigation_budget.action_recommendation}</p>
                </div>
                <div className="water-stat-box">
                  <div className="net-req-num">{dossier.water_irrigation_budget.net_irrigation_requirement_mm} mm</div>
                  <span className="net-req-lbl">Net Irrigation Depth Needed Today</span>
                </div>
              </div>

              <div className="water-metrics-grid">
                <div className="water-card">
                  <span className="w-card-lbl">Reference ET₀ (Hargreaves)</span>
                  <div className="w-card-val">{dossier.water_irrigation_budget.reference_et0_mm_day} mm/day</div>
                  <span className="w-card-sub">Atmospheric evaporative demand</span>
                </div>

                <div className="water-card">
                  <span className="w-card-lbl">Crop Coefficient (Kc)</span>
                  <div className="w-card-val">{dossier.water_irrigation_budget.crop_coefficient_kc}</div>
                  <span className="w-card-sub">{dossier.water_irrigation_budget.growth_stage}</span>
                </div>

                <div className="water-card">
                  <span className="w-card-lbl">Crop ETc (ET₀ × Kc)</span>
                  <div className="w-card-val">{dossier.water_irrigation_budget.crop_evapotranspiration_etc_mm_day} mm/day</div>
                  <span className="w-card-sub">Total crop moisture consumption</span>
                </div>

                <div className="water-card">
                  <span className="w-card-lbl">Effective Precipitation</span>
                  <div className="w-card-val">{dossier.water_irrigation_budget.effective_precipitation_mm} mm</div>
                  <span className="w-card-sub">From {dossier.water_irrigation_budget.daily_rainfall_mm} mm forecast rain</span>
                </div>
              </div>

              {dossier.water_irrigation_budget.water_volume_liters_per_acre > 0 && (
                <div className="pump-calc-card">
                  <h4>⚡ Farm Pumping Energy Calculator</h4>
                  <div className="pump-details-row">
                    <div>
                      <span className="p-lbl">Water Volume Required:</span>
                      <strong className="p-val">{dossier.water_irrigation_budget.water_volume_liters_per_acre.toLocaleString()} Liters / Acre</strong>
                    </div>
                    <div>
                      <span className="p-lbl">Estimated 5HP Pump Run Time:</span>
                      <strong className="p-val">{dossier.water_irrigation_budget.pump_run_hours_5hp} Hours</strong>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 6: APMC MANDI MARKET PRICES & STORAGE */}
          {/* ========================================================= */}
          {activeTab === "mandi" && dossier.mandi_market_intelligence && (
            <div className="mandi-panel">
              <div className="mandi-hero-card">
                <div className="mandi-main-stat">
                  <span className="mandi-commodity">{dossier.mandi_market_intelligence.commodity}</span>
                  <div className="mandi-price-row">
                    <span className="modal-price">₹{dossier.mandi_market_intelligence.modal_price_inr}</span>
                    <span className="price-unit">/ Quintal (Modal)</span>
                    <span className={`trend-badge ${dossier.mandi_market_intelligence.weekly_trend?.toLowerCase()}`}>
                      {dossier.mandi_market_intelligence.trend_arrow} {dossier.mandi_market_intelligence.weekly_trend}
                    </span>
                  </div>
                  <span className="range-text">Wholesale Range: <strong>{dossier.mandi_market_intelligence.price_range_inr}</strong></span>
                </div>

                <div className="msp-stat-box">
                  <span className="msp-lbl">Government MSP:</span>
                  <div className="msp-val">₹{dossier.mandi_market_intelligence.msp_inr_quintal} / qtl</div>
                  <span className="msp-status">✓ Price above support floor</span>
                </div>
              </div>

              <div className="mandi-details-grid">
                <div className="mandi-subcard">
                  <h4 className="mandi-card-title">📍 Key Trading Market Yards (Mandis)</h4>
                  <ul className="market-list">
                    {(dossier.mandi_market_intelligence.key_markets || []).map((mkt, idx) => (
                      <li key={idx}>🏛️ {mkt}</li>
                    ))}
                  </ul>
                </div>

                <div className="mandi-subcard">
                  <h4 className="mandi-card-title">🌾 Post-Harvest Moisture Standard</h4>
                  <p>{dossier.mandi_market_intelligence.post_harvest_advice}</p>
                </div>

                <div className="mandi-subcard full-width">
                  <h4 className="mandi-card-title">📦 Scientific Warehouse & Storage Specification</h4>
                  <p>{dossier.mandi_market_intelligence.storage_standard}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
