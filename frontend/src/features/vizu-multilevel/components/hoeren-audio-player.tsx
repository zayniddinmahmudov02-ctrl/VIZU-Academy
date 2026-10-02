"use client";

import { useEffect, useState } from "react";
import { Headphones } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { getVizuMultilevelHoerenAudioBlobUrl } from "../services/vizu-multilevel-service";

type State = { status: "loading" } | { status: "ready"; url: string } | { status: "unavailable" };

/** Audio player for one Hören Aufgabe. The audio is streamed through an
 * authenticated endpoint and played from a short-lived blob URL — the
 * student never sees a file name, path or script. It never auto-plays: the
 * student starts it. The browser's native controls provide play/pause, the
 * progress bar, duration and volume. */
export default function VizuMultilevelHoerenAudioPlayer({
  attemptId,
  aufgabeNumber,
  hasAudio,
}: {
  attemptId: string;
  aufgabeNumber: number;
  hasAudio: boolean;
}) {
  const { t } = useTranslation();

  return (
    <div className="rounded-2xl bg-surface-hover/60 p-5 ring-1 ring-surface-border">
      <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-text-muted">
        <Headphones size={15} className="text-purple-500" />
        {t("vizuMultilevel.audioTitle")}
      </div>

      {hasAudio ? (
        <StreamedAudio attemptId={attemptId} aufgabeNumber={aufgabeNumber} />
      ) : (
        <p className="py-3 text-sm text-text-muted">{t("vizuMultilevel.audioUnavailable")}</p>
      )}
      <p className="mt-2 text-xs text-text-muted">{t("vizuMultilevel.listeningInstruction")}</p>
    </div>
  );
}

function StreamedAudio({ attemptId, aufgabeNumber }: { attemptId: string; aufgabeNumber: number }) {
  const { t } = useTranslation();
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;
    getVizuMultilevelHoerenAudioBlobUrl(attemptId, aufgabeNumber)
      .then((url) => {
        objectUrl = url;
        if (cancelled) URL.revokeObjectURL(url);
        else setState({ status: "ready", url });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "unavailable" });
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [attemptId, aufgabeNumber]);

  if (state.status === "loading") return <p className="py-3 text-sm text-text-secondary">{t("vizuMultilevel.audioLoading")}</p>;
  if (state.status === "unavailable") return <p className="py-3 text-sm text-text-muted">{t("vizuMultilevel.audioUnavailable")}</p>;
  return <audio key={state.url} controls preload="metadata" controlsList="nodownload noplaybackrate" src={state.url} className="w-full" />;
}
