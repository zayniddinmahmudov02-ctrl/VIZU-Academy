"use client";

import { useRef, useState, type ReactNode } from "react";
import { CornerUpLeft, Reply, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "../global-chat-service";
import { excerpt, type ResolvedReply } from "../reply-preview";
import { endSwipe, moveSwipe, startSwipe, swipeOffset, swipeProgress, type SwipeState } from "../reply-swipe";

const INTERACTIVE = "button, a, input, textarea, select, [role='menu'], [contenteditable='true']";

/** Swipe a message to the left (touch only) to reply. Vertical drags stay
 *  native scrolling (touch-action: pan-y), taps on buttons / links and text
 *  selection are left alone — see reply-swipe.ts for the rules. Mouse and
 *  keyboard users get the Reply button instead. */
export function SwipeToReply({ enabled, onReply, className, children }: { enabled: boolean; onReply: () => void; className?: string; children: ReactNode }) {
  const state = useRef<SwipeState | null>(null);
  const [offset, setOffset] = useState(0);
  const [progress, setProgress] = useState(0);

  function reset() {
    state.current = null;
    setOffset(0);
    setProgress(0);
  }

  return (
    <div className={cn("relative max-w-[85%] touch-pan-y", className)} data-testid="global-chat-swipe"
         onPointerDown={(e) => {
           if (!enabled || e.pointerType !== "touch" || (e.target as Element).closest(INTERACTIVE)) return;
           state.current = startSwipe(e.clientX, e.clientY, e.timeStamp);
         }}
         onPointerMove={(e) => {
           if (!state.current) return;
           const next = moveSwipe(state.current, e.clientX, e.clientY, e.timeStamp, !!window.getSelection()?.toString());
           if (next.cancelled) return reset();
           if (next.axis === "x" && state.current.axis !== "x") {
             try {
               e.currentTarget.setPointerCapture(e.pointerId); // keep the drag when the finger leaves the bubble
             } catch {
               // the pointer is already gone (released / cancelled): the swipe still works without capture
             }
           }
           state.current = next;
           setOffset(swipeOffset(next));
           setProgress(swipeProgress(next));
         }}
         onPointerUp={() => {
           const fire = state.current !== null && endSwipe(state.current);
           reset();
           if (fire) onReply();
         }}
         onPointerCancel={reset}>
      {progress > 0 && (
        <span aria-hidden className="pointer-events-none absolute inset-y-0 -right-9 flex items-center">
          <span className={cn("flex h-7 w-7 items-center justify-center rounded-full bg-accent-blue/15 text-accent-blue", progress >= 1 && "bg-accent-blue text-white")}
                style={{ opacity: progress, transform: `scale(${0.6 + progress * 0.4})` }}>
            <Reply size={14} />
          </span>
        </span>
      )}
      <div style={{ transform: offset ? `translateX(${offset}px)` : undefined }} className={cn(offset === 0 && "transition-transform duration-150")}>
        {children}
      </div>
    </div>
  );
}

/** The quoted original inside a reply bubble; a button that jumps to it. */
export function ReplyQuote({ reply, light, onJump }: { reply: ResolvedReply; light: boolean; onJump: (id: string) => void }) {
  const { t } = useTranslation();
  const box = cn("mb-1 block w-full rounded-lg border-l-2 px-2 py-1 text-left text-[11px]",
    light ? "border-white/70 bg-white/15 text-white/90" : "border-accent-blue/60 bg-accent-blue/5 text-text-secondary");
  if (!reply.available) {
    return <p className={cn(box, "italic")} data-testid="global-chat-reply-quote" data-available="false">{t("globalChat.replyUnavailable")}</p>;
  }
  return (
    <button type="button" onClick={() => onJump(reply.id)} className={cn(box, "hover:opacity-90")} aria-label={t("globalChat.replyJump")}
            data-testid="global-chat-reply-quote" data-available="true">
      <span className={cn("block truncate font-bold", light ? "text-white" : "text-accent-blue")}>{reply.senderName ?? t("globalChat.deletedUser")}</span>
      <span className="line-clamp-2 whitespace-pre-wrap break-words">{reply.excerpt}</span>
    </button>
  );
}

/** Above the input while composing a reply: who and what is answered, X cancels. */
export function ReplyComposerPreview({ message, onCancel }: { message: ChatMessage; onCancel: () => void }) {
  const { t } = useTranslation();
  const name = message.sender?.name ?? t("globalChat.deletedUser");
  return (
    <div className="mb-2 flex items-start gap-2 rounded-xl bg-accent-blue/5 px-3 py-2 ring-1 ring-accent-blue/20" data-testid="global-chat-reply-preview">
      <CornerUpLeft size={14} className="mt-0.5 shrink-0 text-accent-blue" />
      <div className="min-w-0 flex-1 text-xs">
        <p className="truncate font-bold text-accent-blue">{t("globalChat.replyTo", { name })}</p>
        <p className="line-clamp-2 break-words text-text-secondary">{excerpt(message.body ?? "")}</p>
      </div>
      <button type="button" onClick={onCancel} aria-label={t("globalChat.replyCancel")} data-testid="global-chat-reply-cancel"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-text-secondary hover:bg-surface-hover"><X size={14} /></button>
    </div>
  );
}
