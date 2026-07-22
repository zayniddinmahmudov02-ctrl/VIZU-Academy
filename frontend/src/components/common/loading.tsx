"use client";

import { motion } from "framer-motion";

export default function Loading() {
  return (
    <div className="flex h-[400px] items-center justify-center">
      <motion.div
        className="h-10 w-10 rounded-full border-[3px] border-surface-hover border-t-accent-blue"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
      />
    </div>
  );
}
