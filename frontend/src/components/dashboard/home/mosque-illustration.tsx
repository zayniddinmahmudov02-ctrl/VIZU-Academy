type Props = {
  className?: string;
};

/**
 * Stylised Central-Asian mosque/mausoleum silhouette — the recurring
 * illustration motif for the hero banner and the featured course card.
 */
export default function MosqueIllustration({ className }: Props) {
  return (
    <svg viewBox="0 0 200 160" fill="none" className={className}>
      {/* Ground glow */}
      <ellipse cx="100" cy="150" rx="90" ry="8" fill="#000" opacity="0.08" />

      {/* Side minarets */}
      {[24, 176].map((x) => (
        <g key={x}>
          <rect x={x - 6} y={70} width="12" height="70" rx="2" fill="#f0dfa0" opacity="0.9" />
          <path d={`M${x - 8} 70 L${x} 54 L${x + 8} 70 Z`} fill="#2e5aac" />
          <circle cx={x} cy={50} r="3" fill="#d4af37" />
        </g>
      ))}

      {/* Main building body */}
      <rect x="55" y="86" width="90" height="54" rx="4" fill="#fdfaf2" />
      <rect x="55" y="86" width="90" height="54" rx="4" fill="url(#mosque-wall-shade)" />

      {/* Arched doorway */}
      <path d="M92 140 V112 a8 8 0 0 1 16 0 V140 Z" fill="#2e5aac" opacity="0.85" />

      {/* Small side arches */}
      <path d="M66 140 V120 a5 5 0 0 1 10 0 V140 Z" fill="#2e5aac" opacity="0.35" />
      <path d="M124 140 V120 a5 5 0 0 1 10 0 V140 Z" fill="#2e5aac" opacity="0.35" />

      {/* Gold trim */}
      <rect x="55" y="86" width="90" height="4" fill="#d4af37" />

      {/* Central dome */}
      <path
        d="M60 86 C60 56 82 40 100 40 C118 40 140 56 140 86 Z"
        fill="#3563b0"
      />
      <path
        d="M60 86 C60 56 82 40 100 40 C118 40 140 56 140 86 Z"
        fill="url(#mosque-dome-shade)"
      />
      {/* Dome ribs */}
      <g stroke="#1c3f80" strokeWidth="1.4" opacity="0.5">
        <path d="M100 40 V86" />
        <path d="M84 44 C80 58 79 74 82 86" />
        <path d="M116 44 C120 58 121 74 118 86" />
      </g>

      {/* Drum + finial */}
      <rect x="94" y="30" width="12" height="12" rx="2" fill="#f0dfa0" />
      <path d="M96 30 L100 16 L104 30 Z" fill="#d4af37" />
      <circle cx="100" cy="13" r="3" fill="#e4c877" />

      {/* Crescent */}
      <path
        d="M100 4 a5 5 0 1 0 4.2 7.8 A4 4 0 1 1 100 4 Z"
        fill="#d4af37"
      />

      <defs>
        <linearGradient id="mosque-dome-shade" x1="60" y1="40" x2="140" y2="86" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#4a78c9" />
          <stop offset="100%" stopColor="#274d8f" />
        </linearGradient>
        <linearGradient id="mosque-wall-shade" x1="55" y1="86" x2="145" y2="140" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#e4c877" stopOpacity="0.15" />
        </linearGradient>
      </defs>
    </svg>
  );
}
