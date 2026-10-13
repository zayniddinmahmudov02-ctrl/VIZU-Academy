"use client";

import { useCallback, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";

import VideoPlayer from "@/components/lesson-player/video/video-player";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { completeVideo, updateVideoProgress } from "@/features/lessons/services/video-service";
import { lmsKeys } from "@/features/lms/hooks/use-lms";
import type { LmsVideo } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { resolveMediaUrl } from "@/lib/media";

function watermark(user: { id: string; firstName: string | null; lastName: string | null } | null): string | undefined {
  if (!user) return undefined;
  const name = [user.firstName, user.lastName].filter(Boolean).join(" ").trim();
  return name ? `VIZU Academy · ${name} · ${user.id.slice(0, 8)}` : `VIZU Academy · ${user.id.slice(0, 8)}`;
}

/** One lesson video. Positions are reported to the existing video progress
 * API; whether the video counts as watched is decided by the server
 * (POST /videos/complete checks the recorded watch progress) — the player's
 * own "ended" event is only a request. The signed URL is kept stable while
 * the video plays (a refetched lesson brings a new token, which would
 * otherwise restart the player); "retry" switches to the freshest one. */
type Reload = () => Promise<LmsVideo[] | undefined>;

function LmsVideoItem({ lessonId, video, onReload }: { lessonId: string; video: LmsVideo; onReload: Reload }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { user } = useCurrentUser();
  const [src, setSrc] = useState(() => resolveMediaUrl(video.stream_url) ?? video.stream_url);
  const [subtitles, setSubtitles] = useState(() => (video.subtitle_url ? resolveMediaUrl(video.subtitle_url) ?? undefined : undefined));
  const [completed, setCompleted] = useState(Boolean(video.progress?.completed));
  const reporting = useRef(false);
  const inflight = useRef<Promise<void> | null>(null);
  const asked = useRef(false);

  const report = useCallback(
    (position: number, ended: boolean) => {
      if (reporting.current) return;
      reporting.current = true;
      inflight.current = updateVideoProgress(video.id, Math.floor(position), ended)
        .then(() => undefined)
        .catch((err) => console.warn("Failed to report video progress:", err))
        .finally(() => {
          reporting.current = false;
          inflight.current = null;
        });
    },
    [video.id],
  );

  const handleProgress = useCallback(
    (position: number, ended: boolean) => {
      report(position, ended);
      const duration = video.duration_seconds;
      if (completed || asked.current) return;
      if (!ended && !(duration > 0 && position / duration >= 0.7)) return;
      asked.current = true;
      (async () => {
        await inflight.current;
        try {
          const result = await completeVideo(video.id, ended);
          if (result.completed) {
            setCompleted(true);
            queryClient.invalidateQueries({ queryKey: lmsKeys.lesson(lessonId) });
            queryClient.invalidateQueries({ queryKey: ["lms", "level"] });
          } else {
            asked.current = false;
          }
        } catch {
          asked.current = false; // the server did not accept it yet — ask again on the next report
        }
      })();
    },
    [completed, lessonId, queryClient, report, video.duration_seconds, video.id],
  );

  async function retry() {
    // a fresh lesson fetch = freshly signed URLs (the old token may have expired)
    const fresh = (await onReload())?.find((v) => v.id === video.id);
    if (!fresh) return;
    setSrc(resolveMediaUrl(fresh.stream_url) ?? fresh.stream_url);
    setSubtitles(fresh.subtitle_url ? resolveMediaUrl(fresh.subtitle_url) ?? undefined : undefined);
  }

  return (
    <div className="space-y-2" data-testid="lms-video" data-video-id={video.id}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-text-primary">{video.title}</h3>
        {completed && (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-success" data-testid="lms-video-completed">
            <CheckCircle2 size={14} /> {t("lessons.videoCompleted")}
          </span>
        )}
      </div>
      {video.description && <p className="text-sm text-text-secondary">{video.description}</p>}
      <VideoPlayer
        src={src}
        poster={resolveMediaUrl(video.thumbnail_url) ?? undefined}
        initialPosition={video.progress && !video.progress.completed ? video.progress.last_position : 0}
        onProgress={handleProgress}
        watermarkText={watermark(user)}
        onRetryLoad={retry}
        subtitleUrl={subtitles}
      />
    </div>
  );
}

export default function LmsVideos({ lessonId, videos, onReload }: { lessonId: string; videos: LmsVideo[]; onReload: Reload }) {
  if (videos.length === 0) return null;
  return (
    <div className="space-y-6">
      {videos.map((video) => (
        <LmsVideoItem key={video.id} lessonId={lessonId} video={video} onReload={onReload} />
      ))}
    </div>
  );
}
