/* eslint-disable @next/next/no-img-element -- static brand files in /public/branding with a srcset; next/image would only proxy them again */
import { BRAND_LOGO, BRAND_NAME } from "@/constants/brand";

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

/** The official VIZU-DEUTSCH logo image (constants/brand.ts) at `size` px; never stretched or cropped (square, object-contain). */
export function LogoMark({ size = 52, className = "", decorative = false }: { size?: number; className?: string; decorative?: boolean }) {
  return (
    <img
      src={BRAND_LOGO.src}
      srcSet={BRAND_LOGO.srcSet}
      sizes={`${size}px`}
      width={size}
      height={size}
      alt={decorative ? "" : BRAND_NAME}
      draggable={false}
      decoding="async"
      className={`shrink-0 select-none object-contain drop-shadow-[0_6px_14px_rgba(5,12,30,0.28)] ${className}`}
      style={{ width: size, height: size }}
      data-testid="brand-logo"
    />
  );
}

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

  return (
    <div className={isStack ? "flex flex-col items-center gap-3" : "flex items-center gap-3"}>
      {/* Logo: the wordmark below names the brand, so the image is decorative when it is shown */}
      <LogoMark size={size} decorative={showText} />

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
