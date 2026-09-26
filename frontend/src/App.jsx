import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";
import { fetchForecast } from "./services/api";
import SearchBar from "./components/SearchBar";
import LanguageSelector from "./components/LanguageSelector";
import CurrentWeatherHero from "./components/CurrentWeatherHero";
import HourlyWeatherSlider from "./components/HourlyWeatherSlider";
import QuantileForecastList from "./components/QuantileForecastList";
import AgronomicAlerts from "./components/AgronomicAlerts";
import ComparisonMap from "./ComparisonMap";
import SystemStatsFooter from "./components/SystemStatsFooter";
import TrustPanel from "./components/TrustPanel";
import IVRAndSMSModal from "./components/IVRAndSMSModal";
import PrintableBulletin from "./components/PrintableBulletin";
import InsuranceCertificateModal from "./components/InsuranceCertificateModal";
import LiveStormTracker from "./components/LiveStormTracker";
import TerraChatBot from "./components/TerraChatBot";
import AtmosphericConditionsGrid from "./components/AtmosphericConditionsGrid";
import SunMoonAstronomyCard from "./components/SunMoonAstronomyCard";
import MultiModelEnsembleCard from "./components/MultiModelEnsembleCard";
import CropAdvisorySuite from "./components/CropAdvisorySuite";
import { resolveAutoCrop } from "./utils/seasons";

export default function App() {
  // Current active language: Standardized to English for now
  const selectedLang = "en";
  // Default Gram Panchayat: Amdanga (WB_107778, North 24 Parganas) or cached user preference
  const [selectedId, setSelectedId] = useState(() => {
    try {
      return localStorage.getItem("terramind_panchayat_id") || "WB_107778";
    } catch {
      return "WB_107778";
    }
  });

  const [selectedCrop, setSelectedCrop] = useState(() => {
    try {
      const saved = localStorage.getItem("terramind_crop");
      return resolveAutoCrop(new Date(), saved);
    } catch {
      return "paddy";
    }
  });

  const [isLive, setIsLive] = useState(true);

  const [activePanchayat, setActivePanchayat] = useState(() => {
    try {
      const saved = localStorage.getItem("terramind_panchayat_meta");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(() => new Date());
  const [error, setError] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [isIvrModalOpen, setIsIvrModalOpen] = useState(false);
  const [isBulletinOpen, setIsBulletinOpen] = useState(false);
  const [isInsuranceModalOpen, setIsInsuranceModalOpen] = useState(false);
  const [userGps, setUserGps] = useState(() => {
    try {
      const saved = localStorage.getItem("terramind_user_gps");
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });
  const lastFetchTimeRef = useRef(0);

  // Manual or background real-time sync handler
  const handleRefresh = useCallback(
    async (forceBypass = false) => {
      if (isRefreshing) return;
      setIsRefreshing(true);
      try {
        const result = await fetchForecast(selectedId, {
          days: 5,
          lang: selectedLang === "bn" ? "bn" : "en",
          crop: selectedCrop,
          live: isLive,
          refresh: forceBypass,
        });
        setData(result);
        if (result && result.panchayat_id) {
          setActivePanchayat((prev) => {
            if (!prev || prev.panchayat_id !== result.panchayat_id) {
              const meta = {
                panchayat_id: result.panchayat_id,
                panchayat_name: result.panchayat_name,
                block_name: result.block_name,
                district_name: result.district_name,
                latitude: result.latitude ?? result.panchayat_lat,
                longitude: result.longitude ?? result.panchayat_lon,
              };
              try {
                localStorage.setItem("terramind_panchayat_meta", JSON.stringify(meta));
              } catch (e) {
                // ignore
              }
              return meta;
            }
            return prev;
          });
        }
        setLastUpdated(new Date());
        lastFetchTimeRef.current = Date.now();
        setError("");
      } catch (err) {
        console.warn("Weather sync notice:", err);
      } finally {
        setIsRefreshing(false);
      }
    },
    [selectedId, selectedCrop, isLive, selectedLang, isRefreshing]
  );

  // Initial and reactive fetch on dependency change
  useEffect(() => {
    let active = true;

    async function fetchData() {
      try {
        const result = await fetchForecast(selectedId, {
          days: 5,
          lang: selectedLang === "bn" ? "bn" : "en",
          crop: selectedCrop,
          live: isLive,
        });
        if (active) {
          setData(result);
          if (result && result.panchayat_id) {
            setActivePanchayat((prev) => {
              if (!prev || prev.panchayat_id !== result.panchayat_id) {
                const meta = {
                  panchayat_id: result.panchayat_id,
                  panchayat_name: result.panchayat_name,
                  block_name: result.block_name,
                  district_name: result.district_name,
                  latitude: result.latitude ?? result.panchayat_lat,
                  longitude: result.longitude ?? result.panchayat_lon,
                };
                try {
                  localStorage.setItem("terramind_panchayat_meta", JSON.stringify(meta));
                } catch (e) {
                  // ignore
                }
                return meta;
              }
              return prev;
            });
          }
          setLastUpdated(new Date());
          lastFetchTimeRef.current = Date.now();
          setError("");
          if (result.forecast?.length > 0) {
            setSelectedDate(result.forecast[0].date);
          }
          setLoading(false);
        }
      } catch (err) {
        if (active) {
          console.error("Forecast fetch error:", err);
          setError("Unable to connect to the forecast server. Please verify backend service.");
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      active = false;
    };
  }, [selectedId, selectedCrop, isLive, selectedLang]);

  // Real-Time Background Auto-Sync: keep all weather and sub-weather data always up to date
  useEffect(() => {
    // 1. Periodic background sync every 5 minutes (300,000 ms)
    const interval = setInterval(() => {
      handleRefresh(false);
    }, 300000);

    // 2. Re-sync when user switches back to this tab (if more than 3 minutes have passed)
    const handleVisibilityOrFocus = () => {
      if (
        document.visibilityState === "visible" &&
        Date.now() - lastFetchTimeRef.current > 180000
      ) {
        handleRefresh(false);
      }
    };

    window.addEventListener("focus", handleVisibilityOrFocus);
    document.addEventListener("visibilitychange", handleVisibilityOrFocus);

    return () => {
      clearInterval(interval);
      window.removeEventListener("focus", handleVisibilityOrFocus);
      document.removeEventListener("visibilitychange", handleVisibilityOrFocus);
    };
  }, [handleRefresh]);

  const handleSelectPanchayat = (gp) => {
    setLoading(true);
    setActivePanchayat(gp);
    if (gp?.user_gps) {
      setUserGps(gp.user_gps);
    }
    const pid = gp.panchayat_id || `WB_${gp.gp_code}`;
    setSelectedId(pid);
    try {
      localStorage.setItem("terramind_panchayat_id", pid);
      localStorage.setItem("terramind_panchayat_meta", JSON.stringify(gp));
    } catch (e) {
      console.warn("Could not save to localStorage:", e);
    }
  };

  const handleClearPanchayat = () => {
    setLoading(true);
    setActivePanchayat(null);
    setUserGps(null);
    setSelectedId("WB_107778");
    try {
      localStorage.removeItem("terramind_panchayat_id");
      localStorage.removeItem("terramind_panchayat_meta");
      localStorage.removeItem("terramind_user_gps");
      localStorage.removeItem("terramind_last_gps_auto");
    } catch (e) {
      console.warn("Could not clear localStorage:", e);
    }
  };

  const handleCropChange = (crop) => {
    setLoading(true);
    setSelectedCrop(crop);
    try {
      localStorage.setItem("terramind_crop", crop);
    } catch (e) {
      console.warn("Could not save crop to localStorage:", e);
    }
  };

  const handleToggleLive = () => {
    setLoading(true);
    setIsLive((prev) => !prev);
  };

  const handleDateChange = (date) => {
    setSelectedDate(date);
  };

  const handleLanguageChange = (lang) => {
    setSelectedLang(lang);
    try {
      localStorage.setItem("terramind_lang", lang);
    } catch (e) {
      console.warn("Could not save language preference:", e);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="brand-block">
            <h1>TerraMind <span className="brand-title-pipe">|</span> <span className="brand-subtitle-badge">Gram Panchayat Climate Intelligence</span></h1>
            <p>Panchayat-Scale Micro-Climate &amp; Agro-Advisory Intelligence System</p>
          </div>
          <div className="header-right-tools">
            <LanguageSelector />
            <div className="location">
              <span>WEST BENGAL</span> • <span>3,339 GRAM PANCHAYATS</span> • <span>HURDLE ML</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="container">
        {/* Statewide SearchBar with 3,339 GP Autocomplete and District Filter */}
        <SearchBar
          onSelectPanchayat={handleSelectPanchayat}
          activePanchayat={activePanchayat}
          onClear={handleClearPanchayat}
        />

        {/* Full Loader for Initial Cold Start */}
        {loading && !data && (
          <div className="loading">
            <div className="loading-spinner"></div>
            <span>Loading downscaled forecast and agronomic advisories...</span>
          </div>
        )}

        {/* Syncing Indicator for Subsequent Panchayat Switches & Auto-Sync Refresh */}
        {((loading && data) || isRefreshing) && (
          <div className="syncing-badge">
            <div className="syncing-dot"></div>
            <span>
              {isRefreshing
                ? "Refreshing real-time weather stream & micro-downscaling..."
                : "Updating weather intelligence for selected Panchayat..."}
            </span>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <strong>Notice:</strong> {error}
          </div>
        )}

        {/* Weather Intelligence Dashboard (Persists continuously without unmounting) */}
        {data && (
          <>
            {/* Field Accessibility & Disaster Action Toolbar */}
            <div className="field-action-toolbar">
              <div className="toolbar-title-wrap">
                <span className="toolbar-radar-pulse"></span>
                <span className="toolbar-label">FIELD ACCESSIBILITY & DISASTER TOOLS:</span>
              </div>
              <div className="toolbar-buttons-wrap">
                <button
                  type="button"
                  className="field-tool-btn sms-tool-btn"
                  onClick={() => setIsIvrModalOpen(true)}
                  title="Generate 160-Character SMS and Simulated Toll-Free IVR Hotline"
                >
                  📱 160-Char SMS & 1800-IVR
                </button>
                <button
                  type="button"
                  className="field-tool-btn insurance-tool-btn"
                  onClick={() => setIsInsuranceModalOpen(true)}
                  title="Generate PMFBY Parametric Weather Loss Certificate"
                >
                  🛡️ PMFBY Insurance Claim
                </button>
                <button
                  type="button"
                  className="field-tool-btn print-tool-btn"
                  onClick={() => setIsBulletinOpen(true)}
                  title="Print A4 Daily Panchayat Notice Bulletin"
                >
                  🖨️ CSC Notice Sheet (A4)
                </button>
              </div>
            </div>

            {/* Live Bay of Bengal Cyclone & Severe Storm Tracker */}
            <LiveStormTracker
              activePanchayat={activePanchayat}
              panchayatId={selectedId}
            />

            {/* Current Weather Hero Card */}
            <CurrentWeatherHero
              data={data}
              selectedCrop={selectedCrop}
              onCropChange={handleCropChange}
              isLive={isLive}
              onToggleLive={handleToggleLive}
              lastUpdated={lastUpdated}
              isRefreshing={isRefreshing}
              onRefresh={() => handleRefresh(true)}
            />

            {/* AccuWeather-Style Atmospheric Conditions & AQI Grid */}
            <AtmosphericConditionsGrid
              liveWeather={data.live_weather}
              airQuality={data.air_quality}
            />

            {/* Weather.com-Style Sun & Moon Astronomy Card */}
            <SunMoonAstronomyCard
              astronomy={data.astronomy}
              panchayatName={data.panchayat_name}
            />

            {/* Yesterday vs Actual Transparency Trust Panel */}
            <TrustPanel
              panchayatId={selectedId}
              lang={selectedLang}
            />

            {/* 24-Hour Weather & Spray Safety Slider */}
            <HourlyWeatherSlider
              data={data}
              selectedDate={selectedDate}
              onSelectDate={handleDateChange}
              onToggleLive={handleToggleLive}
              lastUpdated={lastUpdated}
              isRefreshing={isRefreshing}
              onRefresh={() => handleRefresh(true)}
            />

            {/* 5-Day Quantile Forecast Horizon */}
            <QuantileForecastList
              forecast={data.forecast || []}
              selectedDate={selectedDate}
              onSelectDate={handleDateChange}
            />

            {/* Meteoblue / Ventusky Multi-Model Weather Ensemble Consensus */}
            <MultiModelEnsembleCard
              ensembleData={data.multi_model_ensemble}
              panchayatName={data.panchayat_name}
            />

            {/* Agronomic Advisory Alerts */}
            <AgronomicAlerts
              advisories={data.advisories || []}
              crop={selectedCrop}
              panchayatName={data.panchayat_name || ""}
              bulletin={data.live_agromet_bulletin}
            />

            {/* World-Class Crop Advisory Suite */}
            <CropAdvisorySuite
              crop={selectedCrop}
              panchayatId={selectedId}
              panchayatName={data.panchayat_name || ""}
              forecastData={data}
            />

            {/* Spatial Forecast & Regional Comparison Map */}
            <ComparisonMap
              data={data}
              forecastDays={data.forecast || []}
              selectedDate={selectedDate}
              onDateChange={handleDateChange}
              onSelectPanchayat={handleSelectPanchayat}
              activePanchayat={activePanchayat}
              userGps={userGps}
            />
          </>
        )}
      </main>

      {/* System Telemetry Footer */}
      <SystemStatsFooter />

      {/* Modals for Machine 2 and Machine 3 Delivery */}
      {data && (
        <>
          <IVRAndSMSModal
            isOpen={isIvrModalOpen}
            onClose={() => setIsIvrModalOpen(false)}
            panchayatId={selectedId}
            crop={selectedCrop}
            lang={selectedLang}
          />
          <PrintableBulletin
            isOpen={isBulletinOpen}
            onClose={() => setIsBulletinOpen(false)}
            data={data}
            crop={selectedCrop}
          />
          <InsuranceCertificateModal
            isOpen={isInsuranceModalOpen}
            onClose={() => setIsInsuranceModalOpen(false)}
            panchayatId={selectedId}
            crop={selectedCrop}
          />
        </>
      )}

      {/* Floating TerraMind AI Agro-Climatic Chatbot */}
      <TerraChatBot
        data={data}
        selectedCrop={selectedCrop}
        activePanchayat={activePanchayat}
      />
    </div>
  );
}