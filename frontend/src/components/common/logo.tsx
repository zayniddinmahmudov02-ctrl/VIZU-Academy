type LogoProps = {
  size?: number;
  showText?: boolean;
  /** "row" = mark + text side by side. "stack" = text under the mark (sidebar header). */
  orientation?: "row" | "stack";
  /** Light gold/white text for the navy sidebar background. */
  dark?: boolean;
  /** Show institute tagline under the logo. */
  tagline?: boolean;
};

/**
 * VIZU Academy logo
 * Visuales Institut für Zukunft und Unterricht
 */
export default function Logo({
  size = 52,
  showText = true,
  orientation = "row",
  dark = false,
  tagline = false,
}: LogoProps) {
  const isStack = orientation === "stack";
  const petals = Array.from({ length: 8 }, (_, i) => i * 45);

  return (
    <div className={isStack ? "flex flex-col items-center gap-3" : "flex items-center gap-3"}>
      {/* Logo */}
      <div
        className="relative flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-navy-900 via-navy-800 to-navy-700 shadow-lg ring-1 ring-accent-gold/40"
        style={{ width: size, height: size }}
      >
        <svg viewBox="0 0 100 100" className="h-[70%] w-[70%]" fill="none">
          <circle cx="50" cy="50" r="46" stroke="#d4af37" strokeOpacity=".35" strokeWidth="1.5" />

          <g stroke="#d4af37" strokeWidth="2">
            <rect x="26" y="26" width="48" height="48" />
            <rect x="26" y="26" width="48" height="48" transform="rotate(45 50 50)" />
          </g>

          <g fill="#d4af37">
            {petals.map((deg) => (
              <ellipse
                key={deg}
                cx="50"
                cy="24"
                rx="2.2"
                ry="6"
                transform={`rotate(${deg} 50 50)`}
              />
            ))}
          </g>

          <circle cx="50" cy="50" r="7" fill="#0e1834" stroke="#d4af37" strokeWidth="1.5" />
          <circle cx="50" cy="50" r="2.6" fill="#e4c877" />
        </svg>
      </div>

      {/* Wordmark */}
      {showText && (
        <div className={isStack ? "text-center" : ""}>
          <h1 className="text-xl font-extrabold leading-none tracking-tight">
            <span className="text-accent-gold">VIZU</span>{" "}
            <span className={dark ? "text-white" : "text-text-primary"}>
              ACADEMY
            </span>
          </h1>

          {tagline ? (
            <p
              className={`mt-2 max-w-[190px] text-center text-[10px] font-medium leading-4 ${
                dark ? "text-white/70" : "text-text-secondary"
              }`}
            >
              Visuales Institut für
              <br />
              Zukunft und Unterricht
            </p>
          ) : (
            <p
              className={`mt-1 text-[11px] font-medium tracking-wide ${
                dark ? "text-white/50" : "text-text-muted"
              }`}
            >
              German Language Academy
            </p>
          )}
        </div>
      )}
    </div>
  );
}