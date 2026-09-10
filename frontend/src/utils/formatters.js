/**
 * Formatting and Agronomic Action Utilities
 */

export function formatForecastDate(dateStr) {
  if (!dateStr) return "";
  const date = new Date(`${dateStr}T00:00:00`);
  return date.toLocaleDateString("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

export function getActionChip(ruleId, rainMm) {
  switch (ruleId) {
    case "no_spray_rain":
      return {
        label: "Do Not Spray",
        type: "danger",
        icon: "🚫",
        desc: "High risk of pesticide wash-off",
      };
    case "heat_stress":
      return {
        label: "Heat Stress Alert",
        type: "warning",
        icon: "☀️",
        desc: "Schedule irrigation early morning",
      };
    case "blast_disease_risk":
      return {
        label: "Blast Risk",
        type: "warning",
        icon: "⚠️",
        desc: "Favorable fungal humidity conditions",
      };
    case "sandy_soil_dry_spell":
      return {
        label: "Irrigate Soil",
        type: "warning",
        icon: "💧",
        desc: "Rapid moisture loss in sandy parcel",
      };
    case "harvest_rain":
      return {
        label: "Protect Harvest",
        type: "danger",
        icon: "🌾",
        desc: "Cover reaped paddy to avoid spoilage",
      };
    case "moderate_rain":
      return {
        label: "Check Drainage",
        type: "info",
        icon: "🌧️",
        desc: "Keep field drainage channels clear",
      };
    case "light_rain":
      return {
        label: "Fertilizer Safe",
        type: "success",
        icon: "✅",
        desc: "Light rain aids nitrogen absorption",
      };
    case "dry_day":
      return {
        label: "Field Work Safe",
        type: "success",
        icon: "🚜",
        desc: "Ideal for spraying and cultivation",
      };
    case "sheath_blight_risk":
      return {
        label: "Sheath Blight Alert",
        type: "warning",
        icon: "⚠️",
        desc: "Inspect lower rice leaf sheaths",
      };
    case "potato_late_blight":
      return {
        label: "Late Blight Alert",
        type: "danger",
        icon: "🥔",
        desc: "High fungal risk; apply Mancozeb",
      };
    case "potato_waterlogging_risk":
      return {
        label: "Drain Potato Beds",
        type: "danger",
        icon: "🚨",
        desc: "Open furrows to stop tuber rot",
      };
    case "mustard_aphid_rust_risk":
      return {
        label: "Mustard Aphid Alert",
        type: "warning",
        icon: "🌼",
        desc: "Inspect siliqua and lower leaves",
      };
    case "jute_stem_rot":
      return {
        label: "Drain Jute Field",
        type: "danger",
        icon: "🌿",
        desc: "Prevent Macrophomina stem rot",
      };
    case "paddy_bph_risk":
      return {
        label: "BPH Pest Watch",
        type: "warning",
        icon: "🌾",
        desc: "Scout rice tiller bases",
      };
    default:
      if (rainMm > 15) {
        return {
          label: "Heavy Rain Caution",
          type: "warning",
          icon: "🌧️",
          desc: "Watch for waterlogging",
        };
      }
      return {
        label: "Normal Activity",
        type: "neutral",
        icon: "🌱",
        desc: "Standard agricultural operations",
      };
  }
}
