import { useState, useEffect, useRef } from "react";
import { searchPanchayats, fetchDistricts, fetchNearestPanchayat } from "../services/api";

export default function SearchBar({ onSelectPanchayat, activePanchayat, onClear }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isLocating, setIsLocating] = useState(false);
  const [locationStatus, setLocationStatus] = useState(null);
  const [permissionState, setPermissionState] = useState(null);
  const [userCoords, setUserCoords] = useState(null);

  // Monitor Geolocation permission state via Permissions API
  useEffect(() => {
    let permObj = null;
    if (typeof navigator !== "undefined" && navigator?.permissions?.query) {
      navigator.permissions
        .query({ name: "geolocation" })
        .then((p) => {
          permObj = p;
          setPermissionState(p.state);
          p.onchange = () => {
            setPermissionState(p.state);
          };
        })
        .catch(() => {
          // Geolocation permission query not supported in some browsers
        });
    }
    return () => {
      if (permObj) {
        permObj.onchange = null;
      }
    };
  }, []);

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

    if (permissionState === "denied") {
      setLocationStatus({
        type: "error",
        message:
          "Location access is currently blocked in your browser. Click the lock/settings icon in your browser URL bar, allow Location access, and click 'Use My Location' again.",
      });
      return;
    }

    setIsLocating(true);
    setLocationStatus(null);

    const geoOptions = {
      enableHighAccuracy: true, // Forces true GPS/GNSS / Wi-Fi positioning
      timeout: 15000,          // 15 seconds to acquire a high-accuracy fix
      maximumAge: 0,           // Force fresh reading without stale cached coordinates
    };

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude, accuracy, altitude } = pos.coords;
          const userGpsData = {
            latitude,
            longitude,
            accuracy: Math.round(accuracy),
            altitude: altitude != null ? Math.round(altitude) : null,
            timestamp: pos.timestamp,
          };
          setUserCoords(userGpsData);

          // Find the nearest Gram Panchayat among all 3,339 GPs
          const { nearest_panchayat } = await fetchNearestPanchayat(latitude, longitude, 3);

          if (nearest_panchayat && nearest_panchayat.panchayat_name) {
            const enrichedPanchayat = {
              ...nearest_panchayat,
              user_gps: userGpsData,
              distance_km: nearest_panchayat.distance_km,
            };

            // Select the Gram Panchayat and trigger downscaled forecast sync
            handleSelect(enrichedPanchayat);

            try {
              localStorage.setItem("terramind_last_gps_auto", "true");
              localStorage.setItem("terramind_user_gps", JSON.stringify(userGpsData));
            } catch (e) {
              // ignore
            }

            const dist = nearest_panchayat.distance_km ?? 0;
            const accStr = accuracy ? `±${Math.round(accuracy)}m` : "High Precision";

            if (dist <= 50) {
              setLocationStatus({
                type: "success",
                message: `GPS located your device (Accuracy: ${accStr}). Nearest Gram Panchayat: ${nearest_panchayat.panchayat_name} (${nearest_panchayat.block_name}, ${nearest_panchayat.district_name}) at ${dist} km. Downscaled forecast auto-selected!`,
                coords: userGpsData,
              });
            } else {
              setLocationStatus({
                type: "success",
                message: `GPS detected (${latitude.toFixed(4)}°N, ${longitude.toFixed(4)}°E, Accuracy: ${accStr}). Nearest West Bengal Gram Panchayat is ${nearest_panchayat.panchayat_name} (${nearest_panchayat.district_name}, ~${dist} km away). Auto-selected for agro-climatic simulation.`,
                coords: userGpsData,
              });
            }
          } else {
            setLocationStatus({
              type: "error",
              message: `No Gram Panchayat found near coordinates (${latitude.toFixed(4)}, ${longitude.toFixed(4)}). Please search manually.`,
            });
          }
        } catch (err) {
          console.error("GPS nearest GP lookup error:", err);
          setLocationStatus({
            type: "error",
            message: "Unable to query nearest Gram Panchayat from backend server. Please verify connection or select manually.",
          });
        } finally {
          setIsLocating(false);
        }
      },
      (err) => {
        console.warn("Geolocation acquisition error:", err);
        setIsLocating(false);
        if (err.code === 1) {
          // PERMISSION_DENIED
          setLocationStatus({
            type: "error",
            message:
              "Location permission denied. Click the site settings icon in your browser address bar to allow location access, or search your Gram Panchayat manually.",
          });
        } else if (err.code === 2) {
          // POSITION_UNAVAILABLE
          setLocationStatus({
            type: "error",
            message:
              "GPS position unavailable. Please check your device location services / Wi-Fi and try again, or search manually.",
          });
        } else if (err.code === 3) {
          // TIMEOUT
          setLocationStatus({
            type: "error",
            message:
              "GPS request timed out while acquiring satellite lock. Please click 'Use My Location' again or search manually.",
          });
        } else {
          setLocationStatus({
            type: "error",
            message: `Location error (${err.message || "Unknown error"}). Please search for your Gram Panchayat manually.`,
          });
        }
      },
      geoOptions
    );
  };

  return (
    <div className="search-bar-wrapper" ref={containerRef}>
      <div className="search-inputs-row">
        {/* District Filter Dropdown */}
        <div className="district-filter-select">
          <label htmlFor="district-select" className="search-label">
            DISTRICT
          </label>
          <select
            id="district-select"
            value={selectedDistrict}
            onChange={(e) => {
              setSelectedDistrict(e.target.value);
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

        {/* GP Name / Block Autocomplete Input */}
        <div className="search-input-container">
          <label htmlFor="gp-search-input" className="search-label">
            GRAM PANCHAYAT SEARCH (3,339 GPs)
          </label>
          <div className="search-input-field">
            <span className="search-icon">🔍</span>
            <input
              id="gp-search-input"
              type="text"
              placeholder="Search by Gram Panchayat or Block (e.g. Banchukamari, Falakata, Amdanga)..."
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
                onClick={handleClear}
                title="Clear search"
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
            className={`gps-location-btn ${isLocating ? "locating" : ""} ${permissionState === "denied" ? "permission-denied" : ""}`}
            onClick={handleUseLocation}
            disabled={isLocating}
            title={
              permissionState === "denied"
                ? "Location access is blocked in browser settings. Click to view instructions."
                : "Auto-detect nearest Gram Panchayat using high-precision device GPS"
            }
          >
            <span className="gps-btn-icon">
              {isLocating ? <span className="gps-radar-spinner"></span> : "📍"}
            </span>
            <span className="gps-btn-text">
              {isLocating ? "Acquiring GPS Fix..." : "Use My Location"}
            </span>
          </button>
        </div>
      </div>

      {/* GPS Location Status Banner */}
      {locationStatus && (
        <div className={`gps-status-banner ${locationStatus.type}`}>
          <div className="gps-status-text">
            <span className="gps-status-symbol">
              {locationStatus.type === "error" ? "⚠️" : "🎯"}
            </span>
            <span>{locationStatus.message}</span>
          </div>
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

      {/* Active GP Breadcrumb Badge */}
      {activePanchayat && (
        <div className="active-gp-card">
          <span className="gp-badge-icon">📍</span>
          <div className="gp-badge-details">
            <div className="gp-badge-title">
              <strong>{activePanchayat.panchayat_name} Gram Panchayat</strong>
              <span className="gp-lgd-tag">LGD {activePanchayat.gp_code}</span>
              {activePanchayat.user_gps?.accuracy && (
                <span className="gps-accuracy-chip" title="Device GPS fix accuracy">
                  🛰️ GPS ±{activePanchayat.user_gps.accuracy}m
                </span>
              )}
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
                  GPS Offset: <strong>{activePanchayat.distance_km} km away</strong>
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
