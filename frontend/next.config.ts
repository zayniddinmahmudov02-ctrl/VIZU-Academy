import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Lets the browser de-minify a production error's stack trace back to
  // real file/line/component names (e.g. React error #310's minified
  // frames like "Object.ol [as useMemo]") instead of requiring a guess —
  // pure DevTools-side diagnostics, no runtime/behavior change, no
  // extra bytes shipped to the page itself (source maps are a separate
  // fetch DevTools makes on demand).
  productionBrowserSourceMaps: true,
};

export default nextConfig;
