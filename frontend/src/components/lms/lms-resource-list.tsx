"use client";

import { Download, ExternalLink, FileText, Image as ImageIcon, Link2 } from "lucide-react";

import type { LmsResource } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { resolveMediaUrl } from "@/lib/media";

import LmsAudioPlayer from "./lms-audio-player";

function size(bytes: number | null): string | null {
  if (!bytes) return null;
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

/** Published resources of one competency (or of the whole lesson). Files are
 * opened only through the backend's signed, short-lived URLs; links are
 * external https pages opened in a new tab. */
export default function LmsResourceList({ resources, onReload }: { resources: LmsResource[]; onReload: () => Promise<LmsResource[] | undefined> }) {
  const { t } = useTranslation();
  if (resources.length === 0) return null;

  async function freshUrl(id: string): Promise<string | null> {
    const r = (await onReload())?.find((x) => x.id === id);
    return r?.file_url ? resolveMediaUrl(r.file_url) : null;
  }

  return (
    <section className="space-y-3" data-testid="lms-resources">
      <h3 className="text-sm font-bold uppercase tracking-wide text-text-muted">{t("lms.materials")}</h3>
      <ul className="space-y-3">
        {resources.map((r) => {
          const url = r.file_url ? resolveMediaUrl(r.file_url) : null;
          const meta = [r.resource_type === "LINK" ? null : r.resource_type, size(r.size_bytes)].filter(Boolean).join(" · ");
          return (
            <li key={r.id} data-testid="lms-resource" data-type={r.resource_type}>
              {r.resource_type === "AUDIO" && url ? (
                <LmsAudioPlayer src={url} title={r.title} onRetry={() => freshUrl(r.id)} />
              ) : r.resource_type === "IMAGE" && url ? (
                <figure className="overflow-hidden rounded-2xl bg-surface-hover/60 p-3 ring-1 ring-surface-border">
                  {/* eslint-disable-next-line @next/next/no-img-element -- signed, short-lived URL; not for the image optimiser */}
                  <img src={url} alt={r.title} className="mx-auto block h-auto max-h-[70vh] w-auto max-w-full object-contain" loading="lazy" />
                  <figcaption className="px-4 py-2 text-sm text-text-secondary">{r.title}</figcaption>
                </figure>
              ) : (
                <div className="flex flex-wrap items-center gap-3 rounded-2xl bg-surface-hover/60 p-4 ring-1 ring-surface-border">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-blue/10 text-accent-blue">
                    {r.resource_type === "LINK" ? <Link2 size={18} /> : r.resource_type === "IMAGE" ? <ImageIcon size={18} /> : <FileText size={18} />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-text-primary">{r.title}</p>
                    {r.description && <p className="text-sm text-text-secondary">{r.description}</p>}
                    {meta && <p className="text-xs text-text-muted">{meta}</p>}
                  </div>
                  {r.resource_type === "LINK" && r.external_url ? (
                    <a href={r.external_url} target="_blank" rel="noopener noreferrer"
                       className="inline-flex items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
                      {t("lms.openLink")} <ExternalLink size={14} />
                    </a>
                  ) : url ? (
                    <a href={url} target="_blank" rel="noopener noreferrer"
                       className="inline-flex items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
                      {r.resource_type === "PDF" ? t("lms.openPdf") : t("lms.download")}
                      {r.resource_type === "PDF" ? <ExternalLink size={14} /> : <Download size={14} />}
                    </a>
                  ) : null}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
