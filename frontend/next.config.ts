import path from "node:path";

import type { NextConfig } from "next";

// This directory (frontend/) is the project root. Without an explicit root,
// Next.js picks the directory of the top-most lockfile it finds — on the
// server a stray /opt/vizu/package-lock.json made it treat /opt/vizu as the
// workspace root. Both settings must point at the same directory.
const projectRoot = path.resolve(__dirname);

const nextConfig: NextConfig = {
  turbopack: {
    root: projectRoot,
  },
  outputFileTracingRoot: projectRoot,
  // `next build` empties and rewrites its output directory. Building into
  // the live `.next` while `next start` serves from it produces missing
  // BUILD_ID / client reference manifests / pages/500.html (HTTP 500s) for
  // the whole build. scripts/deploy-frontend.sh builds into a staging
  // directory via NEXT_DIST_DIR and swaps it in only after a successful
  // build; unset (dev, plain `npm run build`, `next start`) it stays `.next`.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  // Lets the browser de-minify a production error's stack trace back to
  // real file/line/component names (e.g. React error #310's minified
  // frames like "Object.ol [as useMemo]") instead of requiring a guess —
  // pure DevTools-side diagnostics, no runtime/behavior change, no
  // extra bytes shipped to the page itself (source maps are a separate
  // fetch DevTools makes on demand).
  productionBrowserSourceMaps: true,
};

export default nextConfig;
