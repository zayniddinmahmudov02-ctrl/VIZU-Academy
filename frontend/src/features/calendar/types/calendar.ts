export type CalendarEventType = "lesson" | "exam" | "personal" | "other";

export interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  type: CalendarEventType;
  description?: string;
}

export interface CalendarEventInput {
  title: string;
  date: string;
  type: CalendarEventType;
  description?: string;
}
