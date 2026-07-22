"use client";

import { motion } from "framer-motion";
import { BarChart3 } from "lucide-react";

const week = [
  { day: "Mo", value: 0 },
  { day: "Di", value: 0 },
  { day: "Mi", value: 0 },
  { day: "Do", value: 0 },
  { day: "Fr", value: 0 },
  { day: "Sa", value: 0 },
  { day: "So", value: 0 },
];

export default function WeeklyActivity() {
  return (
    <section className="flex h-full flex-col rounded-card bg-surface-card p-5 shadow-[var(--shadow-card)] ring-1 ring-surface-border sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-b from-accent-blue to-brand-600 text-white shadow-[var(--shadow-3d-soft)]">
            <BarChart3 size={20} />
          </div>
          <h2 className="text-base font-bold text-text-primary">Wochenaktivität</h2>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-text-primary">0h</p>
          <p className="text-[11px] text-text-muted">Gesamt</p>
        </div>
      </div>

      {/* Weekly bars */}
      <div className="mt-6 flex flex-1 items-end justify-between gap-2 sm:gap-3">
        {week.map((d, i) => (
          <div key={d.day} className="flex flex-1 flex-col items-center gap-2">
            <div className="flex h-16 w-full items-end overflow-hidden rounded-md bg-surface-hover">
              <motion.div
                className="w-full rounded-md bg-gradient-to-t from-accent-blue to-accent-purple"
                initial={{ height: 0 }}
                animate={{ height: `${Math.max(d.value, 6)}%` }}
                transition={{ duration: 0.5, delay: i * 0.05, ease: "easeOut" }}
              />
            </div>
            <span className="text-[10px] font-medium text-text-muted">{d.day}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
