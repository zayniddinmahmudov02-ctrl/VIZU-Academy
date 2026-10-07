"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Award, Download, Loader2 } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";

import { downloadVizuMultilevelCertificatePdf } from "../services/vizu-multilevel-service";

/** "Zertifikat herunterladen" — the backend builds the PDF from the
 * attempt's stored result; for a below-A1 result a "Kein Zertifikat" note
 * is shown instead (no button). Technical errors are never shown. */
export default function VizuMultilevelCertificateDownload({ attemptId, level }: { attemptId: string; level: string | null }) {
  const { t } = useTranslation();
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);

  if (!level) {
    return (
      <section className="rounded-2xl bg-surface-card p-5 text-center shadow-[var(--shadow-sm)] ring-1 ring-surface-border" data-testid="certificate-none">
        <p className="text-sm font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.certNone")}</p>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t("vizuMultilevel.certNoneBody")}</p>
      </section>
    );
  }

  async function download() {
    setPending(true);
    setFailed(false);
    try {
      await downloadVizuMultilevelCertificatePdf(attemptId);
    } catch {
      setFailed(true);
    } finally {
      setPending(false);
    }
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.3 }}
      className="flex flex-col items-center gap-4 rounded-2xl bg-surface-card p-6 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:flex-row sm:text-left"
      data-testid="certificate-download"
    >
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#0e1834] text-[#d4af37]">
        <Award size={24} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-base font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.certLevel", { level })}</p>
        <p className="text-sm text-slate-600 dark:text-slate-300">{t("vizuMultilevel.certSubtitle")}</p>
        {failed && (
          <p role="alert" className="mt-2 text-sm font-medium text-orange-600">
            {t("vizuMultilevel.certError")}
          </p>
        )}
      </div>
      <Button onClick={download} disabled={pending}>
        {pending ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
        {pending ? t("vizuMultilevel.certGenerating") : t("vizuMultilevel.certDownload")}
      </Button>
    </motion.section>
  );
}
