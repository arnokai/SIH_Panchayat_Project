/**
 * TerraMind Agro-Climatic Seasonal Crop Engine
 *
 * Implements West Bengal agricultural calendar:
 * 1. Kharif (June - October): Aman paddy, Jute (late harvest), Monsoon vegetables.
 *    -> Avoids unseasonal Rabi crops (Potato, Mustard).
 * 2. Rabi (November - March): Potato, Mustard, Winter vegetables, Boro paddy.
 *    -> Avoids unseasonal warm-season Jute.
 * 3. Zaid / Pre-Kharif (April - May): Jute sowing, Summer vegetables, Aus paddy.
 *    -> Avoids unseasonal winter crops.
 */

export const SEASONS_CONFIG = {
  kharif: {
    id: "kharif",
    name: "Kharif (Monsoon & Autumn)",
    nameBn: "খরিফ মরশুম (বর্ষা ও শরৎকালীন)",
    months: [6, 7, 8, 9, 10], // June to October
    primaryCrop: "paddy",
    icon: "🍂",
    tagline: "Monsoon Crop Season",
    activeCrops: [
      {
        id: "paddy",
        name: "Paddy",
        nameBn: "আমন ধান",
        icon: "🌾",
        category: "Staple Cereal",
        isPrimary: true,
        tag: "Primary Staple",
      },
      {
        id: "jute",
        name: "Jute",
        nameBn: "পাট",
        icon: "🌿",
        category: "Commercial Fiber",
        isPrimary: false,
        tag: "Late Harvest / Retting",
      },
      {
        id: "vegetables",
        name: "Vegetables",
        nameBn: "শাকসবজি",
        icon: "🥬",
        category: "Horticulture",
        isPrimary: false,
        tag: "Monsoon Vegetables",
      },
    ],
    inactiveCrops: [
      {
        id: "potato",
        name: "Potato",
        nameBn: "আলু",
        icon: "🥔",
        avoidanceReason:
          "Rabi winter crop. Planting in late monsoon heat (>30°C) and saturated soils causes seed tuber decay.",
      },
      {
        id: "mustard",
        name: "Mustard",
        nameBn: "সরিষা",
        icon: "🌼",
        avoidanceReason:
          "Rabi winter oilseed. Sowing starts late October; rain and high humidity destroy young seedlings.",
      },
    ],
  },
  rabi: {
    id: "rabi",
    name: "Rabi (Winter)",
    nameBn: "রবি মরশুম (শীতকালীন)",
    months: [11, 12, 1, 2, 3], // November to March
    primaryCrop: "potato",
    icon: "❄️",
    tagline: "Winter Crop Season",
    activeCrops: [
      {
        id: "potato",
        name: "Potato",
        nameBn: "আলু",
        icon: "🥔",
        category: "Tuber Cash Crop",
        isPrimary: true,
        tag: "Winter Cash Crop",
      },
      {
        id: "mustard",
        name: "Mustard",
        nameBn: "সরিষা",
        icon: "🌼",
        category: "Oilseed",
        isPrimary: false,
        tag: "Winter Oilseed",
      },
      {
        id: "vegetables",
        name: "Vegetables",
        nameBn: "শীতকালীন সবজি",
        icon: "🥬",
        category: "Horticulture",
        isPrimary: false,
        tag: "Winter Greens",
      },
      {
        id: "paddy",
        name: "Paddy (Boro)",
        nameBn: "বোরো ধান",
        icon: "🌾",
        category: "Staple Cereal",
        isPrimary: false,
        tag: "Boro Sowing",
      },
    ],
    inactiveCrops: [
      {
        id: "jute",
        name: "Jute",
        nameBn: "পাট",
        icon: "🌿",
        avoidanceReason:
          "Warm-season fiber crop. Seeds cannot germinate and seedlings perish in winter temperatures <15°C.",
      },
    ],
  },
  zaid: {
    id: "zaid",
    name: "Zaid (Summer Pre-Monsoon)",
    nameBn: "জায়েদ মরশুম (গ্রীষ্মকালীন)",
    months: [4, 5], // April to May
    primaryCrop: "jute",
    icon: "☀️",
    tagline: "Pre-Monsoon Summer Season",
    activeCrops: [
      {
        id: "jute",
        name: "Jute",
        nameBn: "পাট",
        icon: "🌿",
        category: "Commercial Fiber",
        isPrimary: true,
        tag: "Summer Sowing",
      },
      {
        id: "vegetables",
        name: "Vegetables",
        nameBn: "গ্রীষ্মকালীন সবজি",
        icon: "🥬",
        category: "Horticulture",
        isPrimary: false,
        tag: "Summer Gourds",
      },
      {
        id: "paddy",
        name: "Paddy (Aus)",
        nameBn: "আউশ ধান",
        icon: "🌾",
        category: "Staple Cereal",
        isPrimary: false,
        tag: "Aus / Early Sowing",
      },
    ],
    inactiveCrops: [
      {
        id: "potato",
        name: "Potato",
        nameBn: "আলু",
        icon: "🥔",
        avoidanceReason:
          "Rabi winter tuber. Extreme summer heat (>35°C) prevents tuber initiation.",
      },
      {
        id: "mustard",
        name: "Mustard",
        nameBn: "সরিষা",
        icon: "🌼",
        avoidanceReason:
          "Rabi winter oilseed. Heat causes premature drying and flower sterility.",
      },
    ],
  },
};

/**
 * Get current agricultural season info from a given Date (defaults to today).
 */
export function getCurrentSeason(date = new Date()) {
  const month = (date instanceof Date ? date : new Date(date)).getMonth() + 1; // 1-12

  for (const season of Object.values(SEASONS_CONFIG)) {
    if (season.months.includes(month)) {
      return season;
    }
  }

  // Fallback to Kharif
  return SEASONS_CONFIG.kharif;
}

/**
 * Returns active seasonal crops for given date.
 */
export function getActiveSeasonalCrops(date = new Date()) {
  return getCurrentSeason(date).activeCrops;
}

/**
 * Returns out-of-season / avoided crops for given date.
 */
export function getInactiveSeasonalCrops(date = new Date()) {
  return getCurrentSeason(date).inactiveCrops;
}

/**
 * Resolves crop selection:
 * If savedCrop is active in current season, keep it.
 * Otherwise, auto-select current seasonal primary crop.
 */
export function resolveAutoCrop(date = new Date(), savedCrop = null) {
  const season = getCurrentSeason(date);
  const activeIds = season.activeCrops.map((c) => c.id);

  if (savedCrop && activeIds.includes(savedCrop.toLowerCase().trim())) {
    return savedCrop.toLowerCase().trim();
  }

  return season.primaryCrop;
}
