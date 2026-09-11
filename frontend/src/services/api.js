/**
 * TerraMind API Service
 * Centralized client for all backend endpoints.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Fetch 1-5 day weather forecast and agronomic advisories for a Gram Panchayat.
 *
 * @param {string} panchayatId - Gram Panchayat ID (e.g., "WB_107001" or pilot "A2")
 * @param {Object} options
 * @param {number} [options.days=5] - Number of forecast days (1-5)
 * @param {string} [options.crop="paddy"] - Crop context ("paddy" | "vegetables")
 * @param {boolean} [options.live=true] - Dynamic live weather or offline baseline
 * @param {string} [options.lang="en"] - Language (English)
 * @returns {Promise<Object>} Forecast data payload
 */
export async function fetchForecast(panchayatId, options = {}) {
  const {
    days = 5,
    crop = "paddy",
    live = true,
    lang = "en",
    refresh = false,
  } = options;

  const params = new URLSearchParams({
    panchayat_id: panchayatId,
    days: String(days),
    lang,
    crop,
    live: String(live),
  });

  if (refresh) {
    params.set("refresh", "true");
  }

  const response = await fetch(`${API_BASE}/v1/forecast?${params.toString()}`);

  if (!response.ok) {
    let errorDetail = "Failed to fetch forecast";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail?.error || errJson.detail || errorDetail;
    } catch {
      // ignore parse error
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Search Gram Panchayats across West Bengal by name or block.
 *
 * @param {Object} options
 * @param {string} [options.search=""] - Query string
 * @param {string} [options.district=""] - District filter
 * @param {number} [options.limit=100] - Result limit
 * @returns {Promise<Array>} List of matching Gram Panchayats
 */
export async function searchPanchayats(options = {}) {
  const { search = "", district = "", limit = 100 } = options;

  const params = new URLSearchParams();
  if (search.trim()) params.append("search", search.trim());
  if (district.trim()) params.append("district", district.trim());
  if (limit) params.append("limit", String(limit));

  const response = await fetch(`${API_BASE}/v1/statewide/panchayats?${params.toString()}`);

  if (!response.ok) {
    throw new Error("Failed to search Gram Panchayats");
  }

  const data = await response.json();
  return data.panchayats || [];
}

/**
 * Fetch all 22 West Bengal districts with GP and block counts.
 *
 * @returns {Promise<Array>} List of districts
 */
export async function fetchDistricts() {
  const response = await fetch(`${API_BASE}/v1/statewide/districts`);

  if (!response.ok) {
    throw new Error("Failed to fetch districts");
  }

  const data = await response.json();
  return data.districts || [];
}

/**
 * Fetch data lake scale statistics and verification status.
 *
 * @returns {Promise<Object>} Platform stats
 */
export async function fetchStatewideStats() {
  const response = await fetch(`${API_BASE}/v1/statewide/stats`);

  if (!response.ok) {
    throw new Error("Failed to fetch platform telemetry stats");
  }

  return response.json();
}

/**
 * Fetch pilot Gram Panchayats (A1 - A8).
 *
 * @returns {Promise<Array>} Pilot GP list
 */
export async function fetchPilotPanchayats() {
  const response = await fetch(`${API_BASE}/v1/panchayats`);

  if (!response.ok) {
    throw new Error("Failed to fetch pilot panchayats");
  }

  const data = await response.json();
  return data.panchayats || [];
}

/**
 * Find the nearest Gram Panchayats based on device GPS coordinates.
 *
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {number} [limit=5] - Number of candidate Panchayats to return
 * @returns {Promise<{nearest_panchayat: Object, nearby_panchayats: Array}>} Closest Gram Panchayats with distance_km
 */
export async function fetchNearestPanchayat(lat, lon, limit = 5) {
  const response = await fetch(`${API_BASE}/v1/statewide/nearest?lat=${lat}&lon=${lon}&limit=${limit}`);

  if (!response.ok) {
    throw new Error("Failed to locate nearest Gram Panchayat");
  }

  const data = await response.json();
  return {
    nearest_panchayat: data.nearest_panchayat,
    nearby_panchayats: data.nearby_panchayats || (data.nearest_panchayat ? [data.nearest_panchayat] : []),
  };
}

/**
 * Fetch GeoJSON boundaries for Gram Panchayats in a block or district.
 *
 * @param {Object} options
 * @param {string} [options.block=""] - Block name
 * @param {number|string} [options.gpCode=""] - GP LGD code
 * @param {string} [options.panchayatId=""] - Panchayat ID (e.g. WB_107778)
 * @param {string} [options.district=""] - District name
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
export async function fetchBoundaries(options = {}) {
  const { block = "", gpCode = "", panchayatId = "", district = "" } = options;
  const params = new URLSearchParams();
  if (block) params.append("block", block);
  if (gpCode) params.append("gp_code", String(gpCode));
  if (panchayatId) params.append("panchayat_id", String(panchayatId));
  if (district) params.append("district", district);

  try {
    const response = await fetch(`${API_BASE}/v1/statewide/boundaries?${params.toString()}`);
    if (response.ok) {
      return await response.json();
    }
  } catch (err) {
    console.warn("Could not fetch remote boundaries, attempting fallback:", err);
  }

  // Fallback to static bundled GeoJSON
  try {
    const localRes = await fetch("/data/amdanga_boundaries.json");
    if (localRes.ok) {
      return await localRes.json();
    }
  } catch {
    // fallback
  }

  return { type: "FeatureCollection", features: [] };
}
