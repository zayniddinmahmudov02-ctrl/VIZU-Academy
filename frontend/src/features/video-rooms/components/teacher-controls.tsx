"use client";

import { useState } from "react";
import { MessageSquareOff, MessageSquare, MicOff, MonitorUp, PhoneOff, VolumeX } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { chatPermission, micPermission, muteAll, screenSharePermission } from "../video-rooms-service";
import { errorKey, type RoomMeta } from "../video-room-utils";

function Switch({ on, label, onClick, busy, testId, icon }: { on: boolean; label: string; onClick: () => void; busy: boolean; testId: string; icon: React.ReactNode }) {
  return (
    <button type="button" role="switch" aria-checked={on} disabled={busy} onClick={onClick} data-testid={testId}
            className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-sm text-white hover:bg-white/5 disabled:opacity-50">
      <span className="shrink-0 text-neutral-300">{icon}</span>
      <span className="min-w-0 flex-1">{label}</span>
      <span className={cn("relative h-6 w-10 shrink-0 rounded-full transition-colors", on ? "bg-sky-500" : "bg-white/20")}>
        <span className={cn("absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all", on ? "left-[18px]" : "left-0.5")} />
      </span>
    </button>
  );
}

/** Room-wide teacher switches. The current state comes from the LiveKit room metadata the backend writes, so every
 *  host sees the same; each click goes through the backend, which checks that the caller manages this group. */
export default function TeacherControls({ roomId, meta, onEnd, onError, onDone }: {
  roomId: string;
  meta: RoomMeta;
  onEnd: () => void;
  onError: (key: string) => void;
  onDone?: (key: string) => void;
}) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    try {
      await fn();
      onDone?.("videoRoom.created");
    } catch (e) {
      onError(errorKey(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div data-testid="teacher-controls" className="space-y-1 border-b border-white/10 p-2">
      <p className="px-3 pt-1 text-[11px] font-semibold uppercase tracking-wide text-neutral-400">{t("videoRoom.teacherControls")}</p>
      <button type="button" disabled={busy} onClick={() => run(() => muteAll(roomId, false))} data-testid="teacher-mute-all"
              className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-sm text-white hover:bg-white/5 disabled:opacity-50">
        <VolumeX size={18} className="text-neutral-300" /> {t("videoRoom.muteAll")}
      </button>
      <Switch on={!meta.mic} busy={busy} testId="teacher-lock-mics" icon={<MicOff size={18} />} label={t("videoRoom.lockMics")}
              onClick={() => run(() => micPermission(roomId, !meta.mic))} />
      <Switch on={meta.screenShare} busy={busy} testId="teacher-screen-all" icon={<MonitorUp size={18} />} label={t("videoRoom.allowScreenAll")}
              onClick={() => run(() => screenSharePermission(roomId, !meta.screenShare))} />
      <Switch on={meta.chat} busy={busy} testId="teacher-chat-all" icon={meta.chat ? <MessageSquare size={18} /> : <MessageSquareOff size={18} />}
              label={t("videoRoom.chatForAll")} onClick={() => run(() => chatPermission(roomId, !meta.chat))} />
      <button type="button" onClick={onEnd} data-testid="teacher-end"
              className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-sm font-semibold text-red-400 hover:bg-red-500/10">
        <PhoneOff size={18} /> {t("videoRoom.end")}
      </button>
    </div>
  );
}
