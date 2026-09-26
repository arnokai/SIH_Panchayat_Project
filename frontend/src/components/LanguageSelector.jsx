export const INDIAN_LANGUAGES = [
  { code: "en", name: "English", status: "Active (Official)" },
  { code: "bn", name: "Bengali", status: "Upcoming (Phase 2 Multi-Lingual Engine)" },
  { code: "hi", name: "Hindi", status: "Upcoming (Phase 2 Multi-Lingual Engine)" },
];

export default function LanguageSelector() {
  return (
    <div
      className="language-selector-wrapper"
      title="TerraMind website is standardized in English for all telemetry and advisories"
    >
      <div className="language-select-box">
        <span className="language-globe-icon" aria-hidden="true">🌐</span>
        <span className="language-select-label">Language:</span>
        <span className="language-active-badge">English (Official)</span>
      </div>

      <span className="language-status-chip">
        English Only
      </span>
    </div>
  );
}
