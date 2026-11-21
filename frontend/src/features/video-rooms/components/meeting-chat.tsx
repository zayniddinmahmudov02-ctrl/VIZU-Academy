"use client";

import { useEffect, useRef, useState } from "react";
import { useChat } from "@livekit/components-react";
import { Lock, Send } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { CHAT_MAX, cleanChat } from "../video-room-utils";

type Chat = ReturnType<typeof useChat>;

/** Meeting chat over the LiveKit data channel. The sender is set by the SFU (cannot be faked); messages are not stored.
 *  Sending needs the canPublishData permission, which the teacher can take away (room-wide or per student). */
export default function MeetingChat({ chat, canSend, onError }: { chat: Chat; canSend: boolean; onError: (key: string) => void }) {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const end = useRef<HTMLDivElement>(null);
  const { chatMessages, send, isSending } = chat;

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [chatMessages.length]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const body = cleanChat(text);
    if (!body || !canSend) return;
    try {
      await send(body);
      setText("");
    } catch {
      onError("videoRoom.chatFailed");
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ul data-testid="meeting-chat-list" className="min-h-0 flex-1 space-y-2 overflow-y-auto p-3">
        {chatMessages.length === 0 && <li className="p-4 text-center text-xs text-neutral-400">{t("videoRoom.chatEmpty")}</li>}
        {chatMessages.map((m) => {
          const mine = !!m.from?.isLocal;
          return (
            <li key={m.id} className={cn("flex flex-col", mine ? "items-end" : "items-start")}>
              <span className="px-1 text-[11px] text-neutral-400">
                {mine ? t("videoRoom.you") : m.from?.name || m.from?.identity || "—"} · {new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
              <span data-testid="meeting-chat-message"
                    className={cn("max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-3 py-1.5 text-sm", mine ? "bg-sky-600 text-white" : "bg-neutral-800 text-neutral-100")}>
                {m.message.slice(0, CHAT_MAX * 2)}
              </span>
            </li>
          );
        })}
        <div ref={end} />
      </ul>
      {canSend ? (
        <form onSubmit={submit} className="flex gap-2 border-t border-white/10 p-2">
          <input data-testid="meeting-chat-input" value={text} maxLength={CHAT_MAX} onChange={(e) => setText(e.target.value)}
                 placeholder={t("videoRoom.chatPlaceholder")} aria-label={t("videoRoom.chatPlaceholder")}
                 className="h-11 min-w-0 flex-1 rounded-xl bg-neutral-800 px-3 text-sm text-white outline-none ring-1 ring-white/10 focus:ring-sky-500" />
          <button type="submit" data-testid="meeting-chat-send" disabled={isSending || !text.trim()} aria-label={t("videoRoom.chatSend")}
                  className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-sky-600 text-white disabled:opacity-50">
            <Send size={18} />
          </button>
        </form>
      ) : (
        <p data-testid="meeting-chat-disabled" className="flex items-center gap-2 border-t border-white/10 p-3 text-xs text-neutral-400">
          <Lock size={14} /> {t("videoRoom.chatDisabled")}
        </p>
      )}
    </div>
  );
}
