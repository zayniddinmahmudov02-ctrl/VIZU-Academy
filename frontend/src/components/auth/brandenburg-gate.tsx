interface Props {
  className?: string;
}

/** Stylized line-art silhouette of the Brandenburg Gate — decorative only,
 * not a photo reproduction, to keep the German/Berlin theme without
 * depending on any external image asset. */
export default function BrandenburgGate({ className }: Props) {
  return (
    <svg
      viewBox="0 0 400 220"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <rect x="20" y="188" width="360" height="4" rx="2" fill="currentColor" opacity="0.5" />

      {[40, 96, 152, 208, 264, 320].map((x) => (
        <rect key={x} x={x} y="70" width="16" height="118" rx="2" fill="currentColor" opacity="0.35" />
      ))}

      <rect x="28" y="54" width="344" height="18" rx="2" fill="currentColor" opacity="0.45" />

      <rect x="150" y="30" width="100" height="24" rx="2" fill="currentColor" opacity="0.5" />

      <path
        d="M170 30 L200 10 L230 30 Z"
        fill="currentColor"
        opacity="0.55"
      />

      <rect x="188" y="14" width="24" height="10" rx="1" fill="currentColor" opacity="0.65" />
      <circle cx="200" cy="10" r="5" fill="currentColor" opacity="0.65" />
    </svg>
  );
}
