interface IconProps {
  size?: number;
  className?: string;
}

/** Simplified, generic brand-shaped icons (Lucide dropped brand marks; no new
 *  icon dependency was added — these are minimal, non-trademarked glyphs). */

export function TelegramIcon({ size = 20, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M21.5 3.5 2.75 10.9c-1.05.42-1.04 1.02-.18 1.28l4.8 1.5 1.85 5.66c.23.63.4.88.82.88.35 0 .5-.16.7-.36l1.68-1.63 3.5 2.58c.64.36 1.1.17 1.27-.6l2.9-13.65c.24-1-.24-1.4-.53-1.16Zm-11.7 9.9-1.16-3.87 9.9-6.24c.35-.21.68-.1.42.14l-9.16 9.97Z"
        fill="currentColor"
      />
    </svg>
  );
}

export function InstagramIcon({ size = 20, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" strokeWidth="1.8" />
      <circle cx="12" cy="12" r="4.2" stroke="currentColor" strokeWidth="1.8" />
      <circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" />
    </svg>
  );
}

export function YoutubeIcon({ size = 20, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <rect x="2.5" y="5.5" width="19" height="13" rx="4" stroke="currentColor" strokeWidth="1.8" />
      <path d="M10.5 9.3v5.4l4.6-2.7-4.6-2.7Z" fill="currentColor" />
    </svg>
  );
}
