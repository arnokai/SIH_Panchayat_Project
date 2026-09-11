import { useEffect, useState } from "react";
import "./App.css";
import { fetchForecast } from "./services/api";
import SearchBar from "./components/SearchBar";
import CurrentWeatherHero from "./components/CurrentWeatherHero";
import HourlyWeatherSlider from "./components/HourlyWeatherSlider";
import QuantileForecastList from "./components/QuantileForecastList";
import AgronomicAlerts from "./components/AgronomicAlerts";
import ComparisonMap from "./ComparisonMap";
import SystemStatsFooter from "./components/SystemStatsFooter";

export default function App() {
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
      return localStorage.getItem("terramind_crop") || "paddy";
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
  const [error, setError] = useState("");
  const [selectedDate, setSelectedDate] = useState("");

  useEffect(() => {
    let active = true;

    async function fetchData() {
      try {
        const result = await fetchForecast(selectedId, {
          days: 5,
          lang: "en",
          crop: selectedCrop,
          live: isLive,
        });
        if (active) {
          setData(result);
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
  }, [selectedId, selectedCrop, isLive]);

  const handleSelectPanchayat = (gp) => {
    setLoading(true);
    setActivePanchayat(gp);
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
    setSelectedId("WB_107778");
    try {
      localStorage.removeItem("terramind_panchayat_id");
      localStorage.removeItem("terramind_panchayat_meta");
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

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="brand-block">
            <h1>TerraMind</h1>
            <p>Statewide Panchayat-Level Weather & Agronomic Intelligence</p>
          </div>
          <div className="location">
            <span>WEST BENGAL</span> • <span>3,339 GRAM PANCHAYATS</span> • <span>HURDLE V2 ML</span>
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

        {/* Syncing Indicator for Subsequent Panchayat Switches */}
        {loading && data && (
          <div className="syncing-badge">
            <div className="syncing-dot"></div>
            <span>Updating weather intelligence for selected Panchayat...</span>
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
            {/* Current Weather Hero Card */}
            <CurrentWeatherHero
              data={data}
              selectedCrop={selectedCrop}
              onCropChange={handleCropChange}
              isLive={isLive}
              onToggleLive={handleToggleLive}
            />

            {/* 24-Hour Weather & Spray Safety Slider */}
            <HourlyWeatherSlider
              data={data}
              selectedDate={selectedDate}
              onSelectDate={handleDateChange}
              onToggleLive={handleToggleLive}
            />

            {/* 5-Day Quantile Forecast Horizon */}
            <QuantileForecastList
              forecast={data.forecast || []}
              selectedDate={selectedDate}
              onSelectDate={handleDateChange}
            />

            {/* Agronomic Advisory Alerts */}
            <AgronomicAlerts
              advisories={data.advisories || []}
              crop={selectedCrop}
            />

            {/* Spatial Forecast & Regional Comparison Map */}
            <ComparisonMap
              data={data}
              forecastDays={data.forecast || []}
              selectedDate={selectedDate}
              onDateChange={handleDateChange}
              onSelectPanchayat={handleSelectPanchayat}
              activePanchayat={activePanchayat}
            />
          </>
        )}
      </main>

      {/* System Telemetry Footer */}
      <SystemStatsFooter />
    </div>
  );
}