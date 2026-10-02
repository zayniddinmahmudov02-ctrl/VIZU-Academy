"use client";

import type { ReactNode } from "react";
import { MotionConfig } from "framer-motion";

/** VIZU-Multilevel / VIZU-Mock pages: every animation respects the user's
 * `prefers-reduced-motion` setting (framer-motion then skips transform/
 * layout animations and keeps only opacity changes). */
export default function VizuMultilevelLayout({ children }: { children: ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
