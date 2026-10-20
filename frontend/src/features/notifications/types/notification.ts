export type NotificationType = "information" | "update" | "exam" | "course" | "system";

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  createdAt: string;
  isRead: boolean;
  audioUrl?: string;
}

export interface NotificationInput {
  title: string;
  message: string;
  type: NotificationType;
}

/** One entry of GET /notifications/feed: a personal notification ("p:<id>",
 * single-language title / message) or an admin broadcast ("b:<id>", texts
 * in both languages — the UI shows the active one). Plain text only. */
export interface FeedItem {
  id: string;
  kind: "personal" | "broadcast";
  type: string;
  title: string | null;
  message: string | null;
  title_de: string | null;
  title_uz: string | null;
  message_de: string | null;
  message_uz: string | null;
  created_at: string;
  is_read: boolean;
  is_important: boolean;
  link: { type: "INTERNAL"; path: string } | { type: "EXTERNAL"; url: string } | null;
  audio_url: string | null;
}

export interface FeedPage {
  items: FeedItem[];
  next_before: string | null;
}
