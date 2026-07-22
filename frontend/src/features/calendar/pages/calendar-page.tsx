"use client";

import { useMemo, useState, type FormEvent } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, Plus, Trash2, X } from "lucide-react";

import Button from "@/components/ui/button";
import Drawer from "@/components/ui/drawer";
import Input, { Textarea } from "@/components/ui/input";
import Loading from "@/components/common/loading";
import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { useCalendarEvents } from "../hooks/use-calendar-events";
import { buildMonthGrid, localeFor, toDateKey, weekdayLabels } from "../utils/date-helpers";
import type { CalendarEvent, CalendarEventType } from "../types/calendar";

const EVENT_TYPE_DOT: Record<CalendarEventType, string> = {
  lesson: "bg-accent-blue",
  exam: "bg-danger",
  personal: "bg-accent-purple",
  other: "bg-text-muted",
};

const EVENT_TYPE_LABEL_KEY: Record<CalendarEventType, string> = {
  lesson: "calendar.eventTypeLesson",
  exam: "calendar.eventTypeExam",
  personal: "calendar.eventTypePersonal",
  other: "calendar.eventTypeOther",
};

export default function CalendarPage() {
  const { t, language } = useTranslation();
  const { events, loading, addEvent, removeEvent } = useCalendarEvents();

  const [cursor, setCursor] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [formTitle, setFormTitle] = useState("");
  const [formDate, setFormDate] = useState(() => toDateKey(new Date()));
  const [formDescription, setFormDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const locale = localeFor(language);
  const todayKey = toDateKey(new Date());

  const eventsByDate = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of events) {
      const key = event.date.slice(0, 10);
      const list = map.get(key) ?? [];
      list.push(event);
      map.set(key, list);
    }
    return map;
  }, [events]);

  const monthLabel = new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }).format(
    cursor,
  );
  const weeks = useMemo(() => buildMonthGrid(cursor), [cursor]);
  const selectedDayEvents = eventsByDate.get(selectedDate) ?? [];

  const upcomingEvents = useMemo(
    () =>
      events
        .filter((event) => event.date.slice(0, 10) >= todayKey)
        .sort((a, b) => a.date.localeCompare(b.date))
        .slice(0, 6),
    [events, todayKey],
  );

  function goToPreviousMonth() {
    setCursor((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  }

  function goToNextMonth() {
    setCursor((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  }

  function openAddEventForDay(dateKey: string) {
    setFormDate(dateKey);
    setDrawerOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!formTitle.trim() || !formDate) return;

    try {
      setSubmitting(true);
      await addEvent({
        title: formTitle.trim(),
        date: formDate,
        type: "personal",
        description: formDescription.trim() || undefined,
      });
      setFormTitle("");
      setFormDescription("");
      setDrawerOpen(false);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <Loading />;

  return (
    <div className="space-y-8">
      <PageHeader
        icon={CalendarDays}
        titleKey="calendar.title"
        subtitleKey="calendar.subtitle"
        gradient="from-accent-blue to-purple-600"
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        {/* Month grid */}
        <section className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-7">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold capitalize text-text-primary">{monthLabel}</h2>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={goToPreviousMonth}
                aria-label={t("calendar.previousMonth")}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-surface-hover text-text-secondary transition-colors hover:bg-accent-blue/10 hover:text-accent-blue"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                type="button"
                onClick={goToNextMonth}
                aria-label={t("calendar.nextMonth")}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-surface-hover text-text-secondary transition-colors hover:bg-accent-blue/10 hover:text-accent-blue"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-7 gap-1.5 text-center text-xs font-semibold text-text-muted">
            {weekdayLabels(locale).map((label, i) => (
              <div key={i} className="capitalize">
                {label}
              </div>
            ))}
          </div>

          <div className="mt-2 grid grid-cols-7 gap-1.5">
            {weeks.flat().map((day, i) => {
              if (!day) return <div key={`empty-${i}`} />;

              const key = toDateKey(day);
              const isToday = key === todayKey;
              const isSelected = key === selectedDate;
              const dayEvents = eventsByDate.get(key) ?? [];

              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSelectedDate(key)}
                  className={`flex aspect-square flex-col items-center justify-center gap-1 rounded-xl text-sm font-medium transition-colors duration-150 ${
                    isSelected
                      ? "bg-gradient-to-br from-accent-blue to-purple-600 text-white shadow-md shadow-accent-blue/25"
                      : isToday
                        ? "bg-accent-blue/10 text-accent-blue ring-1 ring-accent-blue/30"
                        : "text-text-primary hover:bg-surface-hover"
                  }`}
                >
                  {day.getDate()}
                  {dayEvents.length > 0 && (
                    <span className="flex gap-0.5">
                      {dayEvents.slice(0, 3).map((event) => (
                        <span
                          key={event.id}
                          className={`h-1.5 w-1.5 rounded-full ${isSelected ? "bg-white" : EVENT_TYPE_DOT[event.type]}`}
                        />
                      ))}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </section>

        {/* Side column */}
        <div className="space-y-6">
          <section className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-base font-bold text-text-primary">{t("calendar.selectedDay")}</h2>
              <Button size="sm" onClick={() => openAddEventForDay(selectedDate)}>
                <Plus size={15} />
                {t("calendar.addEvent")}
              </Button>
            </div>

            <div className="mt-4 space-y-2.5">
              {selectedDayEvents.length === 0 ? (
                <p className="text-sm text-text-muted">{t("calendar.noEvents")}</p>
              ) : (
                selectedDayEvents.map((event) => (
                  <EventRow
                    key={event.id}
                    event={event}
                    onDelete={event.type === "personal" ? () => removeEvent(event.id) : undefined}
                  />
                ))
              )}
            </div>
          </section>

          <section className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
            <h2 className="text-base font-bold text-text-primary">{t("calendar.upcoming")}</h2>
            <div className="mt-4 space-y-2.5">
              {upcomingEvents.length === 0 ? (
                <p className="text-sm text-text-muted">{t("calendar.noUpcoming")}</p>
              ) : (
                upcomingEvents.map((event) => <EventRow key={event.id} event={event} showDate />)
              )}
            </div>
          </section>
        </div>
      </div>

      {/* Add personal event drawer */}
      <Drawer open={drawerOpen} onOpenChange={setDrawerOpen} side="right" className="bg-surface-card">
        <form onSubmit={handleSubmit} className="flex h-full flex-col p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-text-primary">{t("calendar.addEventTitle")}</h2>
            <button
              type="button"
              onClick={() => setDrawerOpen(false)}
              aria-label={t("calendar.close")}
              className="flex h-9 w-9 items-center justify-center rounded-full text-text-secondary transition-colors hover:bg-surface-hover"
            >
              <X size={18} />
            </button>
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">
                {t("calendar.eventTitleLabel")}
              </label>
              <Input
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                placeholder={t("calendar.eventTitlePlaceholder")}
                required
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">
                {t("calendar.eventDateLabel")}
              </label>
              <Input
                type="date"
                value={formDate}
                onChange={(e) => setFormDate(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">
                {t("calendar.eventDescriptionLabel")}
              </label>
              <Textarea
                rows={4}
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
              />
            </div>
          </div>

          <div className="mt-auto flex gap-3 pt-6">
            <Button
              type="button"
              variant="secondary"
              className="flex-1"
              onClick={() => setDrawerOpen(false)}
            >
              {t("calendar.cancel")}
            </Button>
            <Button type="submit" className="flex-1" disabled={submitting}>
              {t("calendar.save")}
            </Button>
          </div>
        </form>
      </Drawer>
    </div>
  );
}

function EventRow({
  event,
  onDelete,
  showDate,
}: {
  event: CalendarEvent;
  onDelete?: () => void;
  showDate?: boolean;
}) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center gap-3 rounded-xl bg-surface-hover/60 px-3.5 py-2.5">
      <span className={`h-2 w-2 shrink-0 rounded-full ${EVENT_TYPE_DOT[event.type]}`} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-text-primary">{event.title}</p>
        <p className="text-xs text-text-muted">
          {showDate && `${event.date.slice(0, 10)} · `}
          {t(EVENT_TYPE_LABEL_KEY[event.type])}
        </p>
      </div>
      {onDelete && (
        <button
          type="button"
          onClick={onDelete}
          aria-label={t("calendar.deleteEvent")}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-danger/10 hover:text-danger"
        >
          <Trash2 size={14} />
        </button>
      )}
    </div>
  );
}
