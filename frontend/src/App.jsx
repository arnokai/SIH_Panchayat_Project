import { useEffect, useState } from "react";
import "./App.css";
import { fetchForecast } from "./services/api";
import SearchBar from "./components/SearchBar";
import CurrentWeatherHero from "./components/CurrentWeatherHero";
import HourlyWeatherSlider from "./components/HourlyWeatherSlider";
import QuantileForecastList from "./components/QuantileForecastList";
import AgronomicAlerts from "./components/AgronomicAlerts";
// ComparisonMap is on hold for GIS spatial model refinement
// import ComparisonMap from "./ComparisonMap";
import SystemStatsFooter from "./components/SystemStatsFooter";

export default function App() {
  // Default Gram Panchayat: Amdanga (WB_107778, North 24 Parganas)
  const [selectedId, setSelectedId] = useState("WB_107778");
  const [selectedCrop, setSelectedCrop] = useState("paddy");
  const [isLive, setIsLive] = useState(true);
  const [activePanchayat, setActivePanchayat] = useState(null);
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
    setSelectedId(gp.panchayat_id || `WB_${gp.gp_code}`);
  };

  const handleClearPanchayat = () => {
    setLoading(true);
    setActivePanchayat(null);
    setSelectedId("WB_107778");
  };

  const handleCropChange = (crop) => {
    setLoading(true);
    setSelectedCrop(crop);
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

        {/* Loading Spinner */}
        {loading && (
          <div className="loading">
            <div className="loading-spinner"></div>
            <span>Loading downscaled forecast and agronomic advisories...</span>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <strong>Notice:</strong> {error}
          </div>
        )}

        {/* Weather Intelligence Dashboard */}
        {data && !loading && (
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

            {/* Note: Spatial Leaflet Map is on hold for GIS spatial model refinement */}
          </>
        )}
      </main>

      {/* System Telemetry Footer */}
      <SystemStatsFooter />
    </div>
  );
}