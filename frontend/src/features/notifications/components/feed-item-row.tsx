"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ExternalLink,
  GraduationCap,
  Info,
  Loader2,
  Megaphone,
  Play,
  Settings as SettingsIcon,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { api } from "@/services/api";
import { useTranslation } from "@/lib/i18n/use-translation";
import { formatRelativeTime } from "../utils/format-relative-time";
import type { FeedItem } from "../types/notification";

const ICON: Record<string, [LucideIcon, string]> = {
  INFO: [Info, "bg-accent-blue/10 text-accent-blue"],
  SUCCESS: [CheckCircle2, "bg-success/10 text-success"],
  WARNING: [AlertTriangle, "bg-warning/10 text-warning"],
  ANNOUNCEMENT: [Megaphone, "bg-accent-purple/10 text-accent-purple"],
  information: [Info, "bg-accent-blue/10 text-accent-blue"],
  update: [Sparkles, "bg-accent-purple/10 text-accent-purple"],
  exam: [GraduationCap, "bg-warning/10 text-warning"],
  course: [BookOpen, "bg-success/10 text-success"],
  system: [SettingsIcon, "bg-text-muted/10 text-text-muted"],
};

/** Title / text of the active UI language (broadcasts carry both). */
export function itemTexts(item: FeedItem, language: string): { title: string; message: string } {
  if (item.kind === "personal") return { title: item.title ?? "", message: item.message ?? "" };
  const uz = language === "uz";
  return { title: (uz ? item.title_uz : item.title_de) ?? item.title_de ?? "", message: (uz ? item.message_uz : item.message_de) ?? item.message_de ?? "" };
}

function safeExternal(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === "https:" || u.protocol === "http:";
  } catch {
    return false;
  }
}

/** One notification: click = mark read + open its page (in-app path or a
 * validated http(s) URL in a new tab). Texts render as plain text. */
export default function FeedItemRow({ item, onRead, onNavigate, full = false }: {
  item: FeedItem;
  onRead: (id: string) => void;
  onNavigate?: () => void;
  full?: boolean;
}) {
  const { t, language } = useTranslation();
  const router = useRouter();
  const [Icon, accent] = ICON[item.type] ?? ICON.INFO;
  const { title, message } = itemTexts(item, language);
  const link = item.link;
  const internal = link?.type === "INTERNAL" && link.path.startsWith("/") && !link.path.startsWith("//") ? link.path : null;
  const external = link?.type === "EXTERNAL" && safeExternal(link.url) ? link.url : null;

  function open() {
    if (!item.is_read) onRead(item.id);
    if (internal) {
      onNavigate?.();
      router.push(internal);
    } else if (external) {
      onNavigate?.();
      window.open(external, "_blank", "noopener,noreferrer");
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={open}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), open())}
      data-testid="notification-item"
      data-read={item.is_read}
      className={`flex w-full cursor-pointer items-start gap-3 rounded-xl px-2 py-2.5 text-left transition-colors hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue ${
        item.is_read ? "" : "bg-accent-blue/5"
      }`}
    >
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${accent}`} aria-hidden="true">
        <Icon size={15} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5">
          <span className={`${full ? "" : "truncate"} text-sm font-semibold text-text-primary`}>{title}</span>
          {item.is_important && (
            <span className="shrink-0 rounded-full bg-danger/10 px-1.5 py-0.5 text-[10px] font-bold uppercase text-danger">{t("notifications.important")}</span>
          )}
          {!item.is_read && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent-blue" aria-label={t("notifications.unread")} />}
        </span>
        <span className={`mt-0.5 block whitespace-pre-line text-xs text-text-secondary ${full ? "" : "line-clamp-2"}`}>{message}</span>
        <span className="mt-1 flex items-center gap-2 text-[11px] text-text-muted">
          {formatRelativeTime(item.created_at, t)}
          {external && <ExternalLink size={11} aria-hidden="true" />}
          {item.audio_url && <AudioFeedbackButton audioUrl={item.audio_url} />}
        </span>
      </span>
    </div>
  );
}

function AudioFeedbackButton({ audioUrl }: { audioUrl: string }) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);

  async function play(event: React.MouseEvent) {
    event.stopPropagation();
    if (loading) return;
    setLoading(true);
    try {
      const response = await api.get(audioUrl, { responseType: "blob" });
      const url = URL.createObjectURL(response.data);
      const audio = new Audio(url);
      audio.addEventListener("ended", () => URL.revokeObjectURL(url));
      await audio.play();
    } catch {
      // playback failure is not worth an error state in a small inline control
    } finally {
      setLoading(false);
    }
  }

  return (
    <button type="button" onClick={play} disabled={loading}
            className="flex items-center gap-1 font-semibold text-accent-blue transition-colors hover:text-accent-blue-hover disabled:opacity-60">
      {loading ? <Loader2 size={11} className="animate-spin" /> : <Play size={11} />}
      {t("header.playFeedback")}
    </button>
  );
}
