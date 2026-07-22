import { api } from "@/services/api";

import type { CalendarEvent, CalendarEventInput } from "../types/calendar";

export async function getCalendarEvents() {
  const response = await api.get<CalendarEvent[]>("/calendar/events");
  return response.data;
}

export async function createCalendarEvent(payload: CalendarEventInput) {
  const response = await api.post<CalendarEvent>("/calendar/events", payload);
  return response.data;
}

export async function deleteCalendarEvent(eventId: string) {
  await api.delete(`/calendar/events/${eventId}`);
}
