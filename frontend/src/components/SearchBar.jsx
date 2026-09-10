import { useState, useEffect, useRef } from "react";
import { searchPanchayats, fetchDistricts, fetchNearestPanchayat } from "../services/api";

export default function SearchBar({ onSelectPanchayat, activePanchayat, onClear }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState(() => activePanchayat?.district_name || "");
  const [districtPanchayats, setDistrictPanchayats] = useState([]);
  const [isLoadingDistrictGPs, setIsLoadingDistrictGPs] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isLocating, setIsLocating] = useState(false);
  const [locationStatus, setLocationStatus] = useState(null);
  const [nearbyCandidates, setNearbyCandidates] = useState([]);

  const containerRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const isSelectingRef = useRef(false);

  // Load district list on mount
  useEffect(() => {
    let mounted = true;
    async function loadDistricts() {
      try {
        const list = await fetchDistricts();
        if (mounted) setDistricts(list);
      } catch (err) {
        console.warn("Could not load districts for search filter:", err);
      }
    }
    loadDistricts();
    return () => {
      mounted = false;
    };
  }, []);

  // Fetch all Panchayats for the selected district (for the direct cascading dropdown)
  useEffect(() => {
    if (!selectedDistrict) {
      return;
    }

    let active = true;

    searchPanchayats({ district: selectedDistrict, limit: 350 })
      .then((list) => {
        if (active) {
          setDistrictPanchayats(list);
          setIsLoadingDistrictGPs(false);
        }
      })
      .catch((err) => {
        console.warn("Could not load district panchayats:", err);
        if (active) setIsLoadingDistrictGPs(false);
      });

    return () => {
      active = false;
    };
  }, [selectedDistrict]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Debounced search trigger for typed queries
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Skip search if text update was triggered programmatically by item selection
    if (isSelectingRef.current) {
      isSelectingRef.current = false;
      return;
    }

    if (!searchTerm.trim()) {
      return;
    }

    debounceTimerRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchPanchayats({
          search: searchTerm.trim(),
          district: selectedDistrict,
          limit: 10,
        });
        setSearchResults(results);
        setIsOpen(results.length > 0);
        setSelectedIndex(-1);
      } catch (err) {
        console.error("Search error:", err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchTerm, selectedDistrict]);

  const handleSelect = (gp) => {
    isSelectingRef.current = true;
    setSearchTerm(gp.panchayat_name);
    setIsOpen(false);
    setSearchResults([]);
    if (gp.district_name && gp.district_name !== selectedDistrict) {
      setSelectedDistrict(gp.district_name);
    }
    onSelectPanchayat(gp);
  };

  const handleKeyDown = (e) => {
    if (!isOpen || searchResults.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < searchResults.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : searchResults.length - 1));
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      handleSelect(searchResults[selectedIndex]);
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const handleClear = () => {
    isSelectingRef.current = true;
    setSearchTerm("");
    setSearchResults([]);
    setIsOpen(false);
    setNearbyCandidates([]);
    setLocationStatus(null);
    if (onClear) onClear();
  };

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus({
        type: "error",
        message: "Geolocation is not supported by your browser.",
      });
      return;
    }

    setIsLocating(true);
    setLocationStatus(null);

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords;
          const { nearest_panchayat, nearby_panchayats } = await fetchNearestPanchayat(latitude, longitude, 5);

          if (nearest_panchayat && nearest_panchayat.panchayat_name) {
            handleSelect(nearest_panchayat);
            setNearbyCandidates(nearby_panchayats || [nearest_panchayat]);
            setLocationStatus({
              type: "success",
              message: `GPS detected closest GP: ${nearest_panchayat.panchayat_name} (${nearest_panchayat.district_name}) ~${nearest_panchayat.distance_km} km away. Tap any nearby candidate below if your farm is in an adjacent Panchayat.`,
            });
          } else {
            setLocationStatus({
              type: "error",
              message: "No Gram Panchayat found near your coordinates.",
            });
          }
        } catch (err) {
          console.error("GPS nearest GP lookup error:", err);
          setLocationStatus({
            type: "error",
            message: "Could not find nearest Gram Panchayat for your location.",
          });
        } finally {
          setIsLocating(false);
        }
      },
      (err) => {
        console.warn("Geolocation error:", err);
        setIsLocating(false);
        if (err.code === 1) {
          setLocationStatus({
            type: "error",
            message: "Location permission denied. Please enable GPS permissions or search manually.",
          });
        } else if (err.code === 2) {
          setLocationStatus({
            type: "error",
            message: "Location position unavailable. Please search manually.",
          });
        } else {
          setLocationStatus({
            type: "error",
            message: "Location request timed out. Please try again or search manually.",
          });
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  };

  return (
    <div className="search-bar-wrapper" ref={containerRef}>
      <div className="search-inputs-row">
        {/* District Filter Dropdown */}
        <div className="district-filter-select">
          <label htmlFor="district-select" className="search-label">
            1. DISTRICT
          </label>
          <select
            id="district-select"
            value={selectedDistrict}
            onChange={(e) => {
              const val = e.target.value;
              setSelectedDistrict(val);
              if (!val) {
                setDistrictPanchayats([]);
                setIsLoadingDistrictGPs(false);
              } else {
                setIsLoadingDistrictGPs(true);
              }
              setIsOpen(false);
            }}
            className="district-select-input"
          >
            <option value="">All 22 Districts</option>
            {districts.map((d) => (
              <option key={d.district_name} value={d.district_name}>
                {d.district_name} ({d.total_panchayats} GPs)
              </option>
            ))}
          </select>
        </div>

        {/* Cascading Gram Panchayat Dropdown (Active when a District is selected) */}
        {selectedDistrict && (
          <div className="district-panchayat-select">
            <label htmlFor="panchayat-dropdown-select" className="search-label">
              2. SELECT GP ({districtPanchayats.length})
            </label>
            <select
              id="panchayat-dropdown-select"
              value={activePanchayat?.district_name?.toLowerCase() === selectedDistrict.toLowerCase() ? (activePanchayat.panchayat_id || `WB_${activePanchayat.gp_code}`) : ""}
              onChange={(e) => {
                const pid = e.target.value;
                const match = districtPanchayats.find((gp) => (gp.panchayat_id || `WB_${gp.gp_code}`) === pid);
                if (match) handleSelect(match);
              }}
              className="district-select-input"
              disabled={isLoadingDistrictGPs}
            >
              <option value="">
                {isLoadingDistrictGPs ? "Loading GPs..." : `-- Choose ${selectedDistrict} GP --`}
              </option>
              {districtPanchayats.map((gp) => (
                <option key={gp.panchayat_id || gp.gp_code} value={gp.panchayat_id || `WB_${gp.gp_code}`}>
                  {gp.panchayat_name} ({gp.block_name})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Universal Search Input */}
        <div className="search-input-container">
          <label htmlFor="gp-search-input" className="search-label">
            {selectedDistrict ? `SEARCH IN ${selectedDistrict.toUpperCase()}` : "UNIVERSAL SEARCH (3,339 GPs)"}
          </label>
          <div className="search-input-field">
            <span className="search-icon">🔍</span>
            <input
              id="gp-search-input"
              type="text"
              placeholder={selectedDistrict ? `Search GP or Block in ${selectedDistrict}...` : "Search by Gram Panchayat or Block name..."}
              value={searchTerm}
              onChange={(e) => {
                const val = e.target.value;
                setSearchTerm(val);
                if (!val.trim()) {
                  setSearchResults([]);
                  setIsOpen(false);
                  setIsSearching(false);
                }
              }}
              onFocus={() => {
                if (searchTerm.trim() && searchResults.length > 0) setIsOpen(true);
              }}
              onKeyDown={handleKeyDown}
              className="statewide-input"
              autoComplete="off"
            />
            {isSearching && <span className="search-spinner">⏳</span>}
            {searchTerm && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => {
                  isSelectingRef.current = true;
                  setSearchTerm("");
                  setSearchResults([]);
                  setIsOpen(false);
                }}
                title="Clear text"
              >
                ✕
              </button>
            )}
          </div>

          {/* Autocomplete Dropdown */}
          {isOpen && searchResults.length > 0 && (
            <ul className="search-dropdown" role="listbox">
              {searchResults.map((gp, idx) => (
                <li
                  key={gp.panchayat_id || gp.gp_code}
                  role="option"
                  aria-selected={idx === selectedIndex}
                  className={`search-result-item ${idx === selectedIndex ? "highlighted" : ""}`}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSelect(gp);
                  }}
                >
                  <div className="search-result-name">
                    <strong>{gp.panchayat_name}</strong>
                    <span className="search-result-meta">
                      {gp.block_name} • {gp.district_name}
                    </span>
                  </div>
                  <div className="search-result-badge">
                    <span>LGD {gp.gp_code}</span>
                    {gp.elevation_m && <span>{Math.round(gp.elevation_m)}m</span>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* GPS Auto-Detect Button */}
        <div className="gps-location-container">
          <label className="search-label">GPS AUTO-DETECT</label>
          <button
            type="button"
            className={`gps-location-btn ${isLocating ? "locating" : ""}`}
            onClick={handleUseLocation}
            disabled={isLocating}
            title="Auto-detect nearest Gram Panchayat using device GPS"
          >
            <span className="gps-btn-icon">{isLocating ? "⏳" : "📍"}</span>
            <span className="gps-btn-text">
              {isLocating ? "Detecting..." : "Use My Location"}
            </span>
          </button>
        </div>
      </div>

      {/* GPS Location Status Banner */}
      {locationStatus && (
        <div className={`gps-status-banner ${locationStatus.type}`}>
          <span className="gps-status-text">
            {locationStatus.type === "error" ? "⚠️" : "✓"} {locationStatus.message}
          </span>
          <button
            type="button"
            className="gps-status-close"
            onClick={() => setLocationStatus(null)}
            title="Dismiss notice"
          >
            ✕
          </button>
        </div>
      )}

      {/* Nearby GPS Candidates Selector Bar */}
      {nearbyCandidates.length > 0 && (
        <div className="nearby-gps-candidates-card">
          <div className="nearby-gps-header">
            <span className="nearby-gps-title">
              📍 <strong>Nearby Panchayats Detected:</strong>
            </span>
            <span className="nearby-gps-hint">
              Tap any candidate below if your farm is in an adjacent Panchayat:
            </span>
            <button
              type="button"
              className="nearby-gps-dismiss"
              onClick={() => setNearbyCandidates([])}
              title="Close nearby suggestions"
            >
              ✕
            </button>
          </div>
          <div className="nearby-gps-chips">
            {nearbyCandidates.map((gp) => {
              const isCurrent = (activePanchayat?.panchayat_id || `WB_${activePanchayat?.gp_code}`) === (gp.panchayat_id || `WB_${gp.gp_code}`);
              return (
                <button
                  key={gp.panchayat_id || gp.gp_code}
                  type="button"
                  className={`nearby-gps-chip ${isCurrent ? "active-chip" : ""}`}
                  onClick={() => handleSelect(gp)}
                >
                  <span className="chip-indicator">{isCurrent ? "✓" : "📍"}</span>
                  <span className="chip-name">{gp.panchayat_name}</span>
                  <span className="chip-block">{gp.block_name}</span>
                  <span className="chip-dist">{gp.distance_km} km</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Active GP Breadcrumb Badge */}
      {activePanchayat && (
        <div className="active-gp-card">
          <span className="gp-badge-icon">📍</span>
          <div className="gp-badge-details">
            <div className="gp-badge-title">
              <strong>{activePanchayat.panchayat_name} Gram Panchayat</strong>
              <span className="gp-lgd-tag">LGD {activePanchayat.gp_code}</span>
            </div>
            <div className="gp-badge-sub">
              <span>District: <strong>{activePanchayat.district_name}</strong></span>
              <span>Block: <strong>{activePanchayat.block_name}</strong></span>
              {activePanchayat.elevation_m && (
                <span>Elevation: <strong>{Math.round(activePanchayat.elevation_m)}m</strong></span>
              )}
              {activePanchayat.soil_type && (
                <span>Soil: <strong>{activePanchayat.soil_type.replace("_", " ")}</strong></span>
              )}
              {activePanchayat.distance_km !== undefined && activePanchayat.distance_km !== null && (
                <span className="gp-distance-tag">
                  GPS Distance: <strong>{activePanchayat.distance_km} km away</strong>
                </span>
              )}
            </div>
          </div>
          <button
            type="button"
            className="gp-badge-close"
            onClick={handleClear}
            title="Reset to default GP"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
