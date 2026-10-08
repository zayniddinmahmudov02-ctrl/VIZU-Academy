/** Geometry for the banner "glass shatter" transition — pure and seeded
 * (no Math.random during render, so it is SSR/hydration-safe and the same
 * seed always yields the same pattern).
 *
 * The banner box is treated as a 0-100 x 0-100 square (percent units, used
 * directly in CSS clip-path polygons). From an impact point, cracks run to
 * points spread along the border; a second "ring" crack splits every wedge
 * into an inner and an outer shard. Each shard carries its own GPU-friendly
 * motion (translate / rotate / scale / opacity only). */

export interface Point {
  x: number;
  y: number;
}

export interface Shard {
  /** CSS clip-path value, e.g. "polygon(10% 0%, ...)" */
  clipPath: string;
  /** Rotation/scale origin = the shard's centroid (percent). */
  origin: string;
  dx: number; // px
  dy: number; // px
  rotate: number; // deg
  /** Seconds after the transition starts. */
  delay: number;
}

export interface ShatterPattern {
  impact: Point;
  shards: Shard[];
  /** Crack lines (percent coords) for the brief "crack" flash. */
  cracks: [Point, Point][];
}

/** mulberry32 — tiny deterministic PRNG. */
function prng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Point on the border for a perimeter parameter t in [0, 400). */
function borderPoint(t: number): Point {
  const u = ((t % 400) + 400) % 400;
  if (u < 100) return { x: u, y: 0 };
  if (u < 200) return { x: 100, y: u - 100 };
  if (u < 300) return { x: 300 - u, y: 100 };
  return { x: 0, y: 400 - u };
}

/** Box corners strictly between two perimeter parameters (walking forward). */
function cornersBetween(t0: number, t1: number): Point[] {
  const out: Point[] = [];
  for (const c of [100, 200, 300, 400]) {
    for (const shift of [0, 400]) {
      const cc = c + shift;
      if (cc > t0 && cc < t1) out.push(borderPoint(cc));
    }
  }
  return out;
}

const pct = (p: Point) => `${p.x.toFixed(2)}% ${p.y.toFixed(2)}%`;

function centroid(points: Point[]): Point {
  const n = points.length;
  return { x: points.reduce((s, p) => s + p.x, 0) / n, y: points.reduce((s, p) => s + p.y, 0) / n };
}

export const SHATTER_WEDGES = 9; // -> 18 shards

export function shatterPattern(seed: number, wedges = SHATTER_WEDGES): ShatterPattern {
  const rand = prng(seed * 7919 + 17);
  const impact = { x: 38 + rand() * 24, y: 36 + rand() * 22 };

  // Border points, roughly evenly spread, with jitter; sorted along the perimeter.
  const offset = rand() * 400;
  const ts = Array.from({ length: wedges }, (_, i) => offset + ((i + 0.15 + rand() * 0.7) / wedges) * 400).sort((a, b) => a - b);
  const border = ts.map(borderPoint);
  const ring = border.map((b) => {
    const r = 0.32 + rand() * 0.2;
    return { x: impact.x + (b.x - impact.x) * r, y: impact.y + (b.y - impact.y) * r };
  });

  const shards: Shard[] = [];
  const cracks: [Point, Point][] = [];

  for (let i = 0; i < wedges; i++) {
    const j = (i + 1) % wedges;
    const t0 = ts[i];
    const t1 = j === 0 ? ts[0] + 400 : ts[j];
    const inner = [impact, ring[i], ring[j]];
    const outer = [ring[i], border[i], ...cornersBetween(t0, t1), border[j], ring[j]];
    cracks.push([impact, border[i]], [ring[i], ring[j]]);

    for (const [poly, isInner] of [
      [inner, true],
      [outer, false],
    ] as const) {
      const c = centroid([...poly]);
      const vx = c.x - impact.x;
      const vy = c.y - impact.y;
      const len = Math.hypot(vx, vy) || 1;
      const push = (isInner ? 26 : 46) + rand() * 34; // px outward
      shards.push({
        clipPath: `polygon(${poly.map(pct).join(", ")})`,
        origin: pct(c),
        dx: (vx / len) * push,
        dy: (vy / len) * push + 28 + rand() * 36, // a little gravity
        rotate: (rand() - 0.5) * (isInner ? 34 : 22),
        // shards near the impact break first
        delay: 0.09 + (len / 100) * 0.12 + rand() * 0.04,
      });
    }
  }
  return { impact, shards, cracks };
}
