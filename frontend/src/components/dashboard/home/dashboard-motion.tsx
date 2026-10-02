"use client";

import type { ReactNode } from "react";
import { MotionConfig } from "framer-motion";

/** Dashboard animations honour `prefers-reduced-motion` (framer-motion then
 * skips transform animations and keeps only opacity changes). */
export default function DashboardMotion({ children }: { children: ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
