import { useState, useEffect, useRef } from "react";
import { searchPanchayats, fetchDistricts } from "../services/api";

export default function SearchBar({ onSelectPanchayat, activePanchayat, onClear }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const containerRef = useRef(null);
  const debounceTimerRef = useRef(null);

  // Load district list on mount for the district filter dropdown
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

  // Debounced search trigger
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(async () => {
      if (!searchTerm.trim() && !selectedDistrict) {
        setSearchResults([]);
        setIsOpen(false);
        setIsSearching(false);
        return;
      }

      setIsSearching(true);
      try {
        const results = await searchPanchayats({
          search: searchTerm.trim(),
          district: selectedDistrict,
          limit: 8,
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
    setSearchTerm("");
    setSearchResults([]);
    setIsOpen(false);
    if (onClear) onClear();
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
              setIsOpen(true);
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
              onChange={(e) => setSearchTerm(e.target.value)}
              onFocus={() => {
                if (searchResults.length > 0) setIsOpen(true);
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
                  onClick={() => handleSelect(gp)}
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
      </div>

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
