import { useId } from "react";

import { resolveMediaUrl } from "@/lib/media";

/** Disc colours of the medal presets (admin: icon_color). The emblem is always gold. */
const COLORS: Record<string, [string, string, string]> = {
  green: ["#34d399", "#059669", "#065f46"],
  blue: ["#60a5fa", "#2563eb", "#1e3a8a"],
  purple: ["#c084fc", "#7c3aed", "#4c1d95"],
  gold: ["#fde68a", "#d97706", "#92400e"],
  red: ["#fca5a5", "#dc2626", "#7f1d1d"],
  teal: ["#5eead4", "#0d9488", "#134e4a"],
};

/** Gold emblems in a 64×64 box centred on (32, 32) (admin: icon_preset). */
function Emblem({ preset, fill }: { preset: string; fill: string }) {
  switch (preset) {
    case "star":
      return <path d="M32 17l4.4 9.6 10.5 1.1-7.8 7.1 2.2 10.3L32 39.9 22.7 45.1l2.2-10.3-7.8-7.1 10.5-1.1z" fill={fill} />;
    case "trophy":
      return (
        <g fill={fill}>
          <path d="M23 19h18v8a9 9 0 0 1-18 0z" />
          <path d="M19 21h4v4a4 4 0 0 1-4-4zM45 21h-4v4a4 4 0 0 0 4-4z" />
          <rect x="29.5" y="35" width="5" height="6" />
          <rect x="24" y="41" width="16" height="4" rx="1.5" />
        </g>
      );
    case "book":
      return (
        <g fill={fill}>
          <path d="M18 21c5-2 10-1 13 2v21c-3-3-8-4-13-2z" />
          <path d="M46 21c-5-2-10-1-13 2v21c3-3 8-4 13-2z" />
        </g>
      );
    case "flame":
      return <path d="M32 15c3 6 9 9 9 17a9 9 0 0 1-18 0c0-4 2-7 4-9 0 3 1 5 3 6-1-6 0-10 2-14z" fill={fill} />;
    case "crown":
      return <path d="M18 41l2-17 7 7 5-11 5 11 7-7 2 17z" fill={fill} />;
    case "rocket":
    default:
      return (
        <g>
          {/* exhaust flame */}
          <path d="M28.5 41.5c0 4 1.6 7.2 3.5 9 1.9-1.8 3.5-5 3.5-9z" fill="#fb923c" />
          {/* fins */}
          <path d="M26 33l-5.5 6.5v3.2l5.5-2.7zM38 33l5.5 6.5v3.2l-5.5-2.7z" fill={fill} />
          {/* body */}
          <path d="M32 13c4.8 3.6 7 9.4 7 16.5V40a2 2 0 0 1-2 2H27a2 2 0 0 1-2-2V29.5c0-7.1 2.2-12.9 7-16.5z" fill={fill} />
          {/* window */}
          <circle cx="32" cy="27" r="3.6" fill="#065f46" stroke="#fff7d6" strokeWidth="1.4" />
          <path d="M32 13c4.8 3.6 7 9.4 7 16.5" fill="none" stroke="#fff7d6" strokeOpacity=".55" strokeWidth="1.2" />
        </g>
      );
  }
}

/** A medal. `earned=false` renders it greyed out with a lock, so earned and
 * open medals are told apart at a glance — also at 32 px. An uploaded image
 * (admin) replaces the drawn medal. */
export default function MedalIcon({
  preset,
  color,
  imageUrl,
  earned,
  size = 56,
  title,
}: {
  preset: string;
  color: string;
  imageUrl?: string | null;
  earned: boolean;
  size?: number;
  title?: string;
}) {
  const id = useId().replace(/:/g, "");
  const [light, mid, dark] = COLORS[color] ?? COLORS.green;
  const image = resolveMediaUrl(imageUrl ?? null);
  const dim = earned ? "" : "grayscale opacity-45";

  return (
    <span className="relative inline-flex shrink-0" style={{ width: size, height: size }} role="img" aria-label={title}>
      {image ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={image} alt="" className={`h-full w-full rounded-full object-cover ${dim}`} />
      ) : (
        <svg viewBox="0 0 64 64" width={size} height={size} className={dim} aria-hidden="true">
          <defs>
            <radialGradient id={`d${id}`} cx="35%" cy="30%" r="75%">
              <stop offset="0%" stopColor={light} />
              <stop offset="60%" stopColor={mid} />
              <stop offset="100%" stopColor={dark} />
            </radialGradient>
            <linearGradient id={`g${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#fde68a" />
              <stop offset="55%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#b45309" />
            </linearGradient>
          </defs>
          {/* gold rim + coloured disc */}
          <circle cx="32" cy="32" r="31" fill={`url(#g${id})`} />
          <circle cx="32" cy="32" r="27" fill={`url(#d${id})`} />
          <circle cx="32" cy="32" r="27" fill="none" stroke="#000" strokeOpacity=".12" strokeWidth="1" />
          <Emblem preset={preset} fill={`url(#g${id})`} />
        </svg>
      )}
      {!earned && (
        <span className="absolute -bottom-0.5 -right-0.5 flex h-[38%] w-[38%] items-center justify-center rounded-full bg-surface-card text-text-muted shadow ring-1 ring-surface-border">
          <svg viewBox="0 0 24 24" className="h-[60%] w-[60%]" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden="true">
            <rect x="5" y="11" width="14" height="10" rx="2" />
            <path d="M8 11V8a4 4 0 0 1 8 0v3" />
          </svg>
        </span>
      )}
    </span>
  );
}
