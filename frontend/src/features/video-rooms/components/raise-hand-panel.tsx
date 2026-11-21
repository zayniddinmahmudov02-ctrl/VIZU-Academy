"use client";

import { useState } from "react";
import { Hand } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { raiseHand } from "../video-rooms-service";
import { errorKey } from "../video-room-utils";

export interface RaisedHand { identity: string; name: string; hand: string }

/** Raised hands in the order they went up. The teacher can lower any hand (backend: hosts only lower others' hands). */
export default function RaiseHandPanel({ roomId, hands, isHost, onError }: {
  roomId: string;
  hands: RaisedHand[];
  isHost: boolean;
  onError: (key: string) => void;
}) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState<string | null>(null);

  async function lower(identity: string) {
    setBusy(identity);
    try {
      await raiseHand(roomId, false, identity);
    } catch (e) {
      onError(errorKey(e));
    } finally {
      setBusy(null);
    }
  }

  if (hands.length === 0) return <p className="p-6 text-center text-sm text-neutral-400">{t("videoRoom.noHands")}</p>;
  return (
    <ol data-testid="hands-list" className="divide-y divide-white/5">
      {hands.map((h, i) => (
        <li key={h.identity} data-testid="hand-row" className="flex items-center gap-3 px-3 py-2.5">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-400 text-xs font-bold text-black">{i + 1}</span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium text-white">{h.name}</span>
            <span className="text-[11px] text-neutral-400">{new Date(h.hand).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>
          </span>
          {isHost && (
            <button type="button" disabled={busy === h.identity} onClick={() => lower(h.identity)} data-testid="hand-lower"
                    className="inline-flex min-h-9 items-center gap-1 rounded-lg bg-white/10 px-2.5 text-xs font-semibold text-white hover:bg-white/20 disabled:opacity-50">
              <Hand size={14} /> {t("videoRoom.lowerHand")}
            </button>
          )}
        </li>
      ))}
    </ol>
  );
}
