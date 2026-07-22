"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CalendarDays } from "lucide-react";

import Popover from "@/components/ui/popover";
import { useTranslation } from "@/lib/i18n/use-translation";
import { buildMonthGrid, localeFor, toDateKey, weekdayLabels } from "../utils/date-helpers";

export default function CalendarDropdown() {
  const { t, language } = useTranslation();
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const locale = localeFor(language);
  const todayKey = toDateKey(now);
  const cursor = new Date(now.getFullYear(), now.getMonth(), 1);
  const weeks = buildMonthGrid(cursor);

  const dateLabel = new Intl.DateTimeFormat(locale, {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(now);
  const timeLabel = new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit" }).format(
    now,
  );
  const monthLabel = new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }).format(
    cursor,
  );

  return (
    <Popover
      trigger={
        <span
          aria-label={t("header.calendarAria")}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-card text-text-secondary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:text-accent-blue"
        >
          <CalendarDays size={15} />
        </span>
      }
    >
      <div className="text-center">
        <p className="text-2xl font-bold tabular-nums text-text-primary">{timeLabel}</p>
        <p className="mt-1 text-sm capitalize text-text-secondary">{dateLabel}</p>
      </div>

      <div className="mt-4 border-t border-surface-border pt-4">
        <p className="mb-3 text-center text-sm font-semibold capitalize text-text-primary">
          {monthLabel}
        </p>

        <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-semibold text-text-muted">
          {weekdayLabels(locale).map((label, i) => (
            <div key={i} className="capitalize">
              {label}
            </div>
          ))}
        </div>

        <div className="mt-1 grid grid-cols-7 gap-1">
          {weeks.flat().map((day, i) => {
            if (!day) return <div key={`empty-${i}`} />;

            const key = toDateKey(day);
            const isToday = key === todayKey;

            return (
              <div
                key={key}
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs ${
                  isToday
                    ? "bg-gradient-to-br from-accent-blue to-purple-600 font-bold text-white shadow-md shadow-accent-blue/25"
                    : "text-text-secondary"
                }`}
              >
                {day.getDate()}
              </div>
            );
          })}
        </div>
      </div>

      <Link
        href="/calendar"
        className="mt-4 flex items-center justify-center rounded-button bg-surface-hover px-4 py-2.5 text-sm font-semibold text-accent-blue transition-colors hover:bg-accent-blue/10"
      >
        {t("calendar.title")}
      </Link>
    </Popover>
  );
}
