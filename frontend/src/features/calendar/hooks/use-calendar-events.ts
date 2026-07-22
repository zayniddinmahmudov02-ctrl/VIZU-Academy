"use client";

import { useCallback, useEffect, useState } from "react";

import { CALENDAR_API_ENABLED } from "@/constants/feature-flags";
import {
  createCalendarEvent,
  deleteCalendarEvent,
  getCalendarEvents,
} from "../services/calendar-service";
import type { CalendarEvent, CalendarEventInput } from "../types/calendar";

interface UseCalendarEventsResult {
  events: CalendarEvent[];
  loading: boolean;
  addEvent: (payload: CalendarEventInput) => Promise<void>;
  removeEvent: (eventId: string) => Promise<void>;
}

export function useCalendarEvents(): UseCalendarEventsResult {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const load = useCallback(async () => {
    if (!CALENDAR_API_ENABLED) {
      setEvents([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await getCalendarEvents();
      setEvents(data);
    } catch (err) {
      // Backend not deployed yet or genuinely no events — either way, the
      // page just shows its empty state rather than an error.
      console.warn("Failed to load calendar events:", err);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function addEvent(payload: CalendarEventInput) {
    const created = await createCalendarEvent(payload);
    setEvents((prev) => [...prev, created]);
  }

  async function removeEvent(eventId: string) {
    await deleteCalendarEvent(eventId);
    setEvents((prev) => prev.filter((event) => event.id !== eventId));
  }

  return { events, loading, addEvent, removeEvent };
}
