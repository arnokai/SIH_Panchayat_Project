/**
 * Self-contained SVG Weather Icons
 * Guarantees zero external network dependencies, zero broken images,
 * and zero "Weath condit" text wrapping glitches.
 */
export default function WeatherIcon({ code, isDaylight = true, className = "", size = 36 }) {
  const w = size;
  const h = size;

  // Clear Sky / Sunny
  if (code === 0 || code == null) {
    if (isDaylight) {
      return (
        <svg
          viewBox="0 0 48 48"
          width={w}
          height={h}
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={className}
          aria-hidden="true"
        >
          <circle cx="24" cy="24" r="10" fill="#f59e0b" />
          <path
            d="M24 6v4m0 28v4M6 24h4m28 0h4m-7.2-10.8l2.8-2.8M11.4 36.6l2.8-2.8m0-19.6l-2.8-2.8m25.2 25.2l-2.8-2.8"
            stroke="#f59e0b"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
      );
    }
    return (
      <svg
        viewBox="0 0 48 48"
        width={w}
        height={h}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-hidden="true"
      >
        <path
          d="M30 9a14 14 0 109 21.5A16 16 0 0130 9z"
          fill="#38bdf8"
        />
        <circle cx="36" cy="14" r="1.5" fill="#fef08a" />
        <circle cx="28" cy="11" r="1" fill="#fef08a" />
      </svg>
    );
  }

  // Partly Cloudy (Codes 1 - 3)
  if (code >= 1 && code <= 3) {
    if (isDaylight) {
      return (
        <svg
          viewBox="0 0 48 48"
          width={w}
          height={h}
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={className}
          aria-hidden="true"
        >
          <circle cx="18" cy="18" r="8" fill="#f59e0b" />
          <path
            d="M18 5v3m-9.2 3.8l2.1 2.1M5 18h3m2.8 9.2l2.1-2.1"
            stroke="#f59e0b"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <path
            d="M36 34a8 8 0 00-7.3-11.2A11 11 0 0017 27a7 7 0 002 13.7h17A6 6 0 0036 34z"
            fill="#94a3b8"
          />
          <path
            d="M38 36a7 7 0 00-6.4-9.8A9.6 9.6 0 0021.4 30 6.1 6.1 0 0023.2 42H38a5.2 5.2 0 000-10.4z"
            fill="#cbd5e1"
          />
        </svg>
      );
    }
    return (
      <svg
        viewBox="0 0 48 48"
        width={w}
        height={h}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-hidden="true"
      >
        <path
          d="M22 10a11 11 0 00-8 15 12 12 0 018-15z"
          fill="#38bdf8"
        />
        <path
          d="M38 36a7 7 0 00-6.4-9.8A9.6 9.6 0 0021.4 30 6.1 6.1 0 0023.2 42H38a5.2 5.2 0 000-10.4z"
          fill="#94a3b8"
        />
        <path
          d="M38 37a6 6 0 00-5.5-8.4A8.2 8.2 0 0024 32a5.2 5.2 0 001.5 10.2H38a4.5 4.5 0 000-9z"
          fill="#cbd5e1"
        />
      </svg>
    );
  }

  // Fog / Mist (Codes 45, 48)
  if (code === 45 || code === 48) {
    return (
      <svg
        viewBox="0 0 48 48"
        width={w}
        height={h}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-hidden="true"
      >
        <path
          d="M10 16h28M8 22h32M12 28h24M8 34h32"
          stroke="#94a3b8"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  // Rain / Drizzle / Showers (Codes 51 - 67, 80 - 82)
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) {
    return (
      <svg
        viewBox="0 0 48 48"
        width={w}
        height={h}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-hidden="true"
      >
        <path
          d="M37 25a7 7 0 00-6.5-9.3A9.2 9.2 0 0021 20a6.1 6.1 0 001.6 12H37a5.2 5.2 0 000-10.5z"
          fill="#94a3b8"
        />
        <path
          d="M17 34l-2 7m8-7l-2 7m8-7l-2 7"
          stroke="#0284c7"
          strokeWidth="2.8"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  // Thunderstorm (Code 95+)
  if (code >= 95) {
    return (
      <svg
        viewBox="0 0 48 48"
        width={w}
        height={h}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-hidden="true"
      >
        <path
          d="M37 23a7 7 0 00-6.5-9.3A9.2 9.2 0 0021 18a6.1 6.1 0 001.6 12H37a5.2 5.2 0 000-10.5z"
          fill="#64748b"
        />
        <path
          d="M24 26l-4 8h5l-2 9 8-11h-5l3-6h-5z"
          fill="#eab308"
        />
      </svg>
    );
  }

  // Default: Cloud
  return (
    <svg
      viewBox="0 0 48 48"
      width={w}
      height={h}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M34 26a8 8 0 00-7.5-10.6A10.5 10.5 0 0016 20a7 7 0 001.8 13.8H34a6 6 0 000-12z"
        fill="#94a3b8"
      />
      <path
        d="M38 34a8 8 0 00-7.5-10.6A10.5 10.5 0 0020 28a7 7 0 001.8 13.8H38a6 6 0 000-12z"
        fill="#cbd5e1"
      />
    </svg>
  );
}
