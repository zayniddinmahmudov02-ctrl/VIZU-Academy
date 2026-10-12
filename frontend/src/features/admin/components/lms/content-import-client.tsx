"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, Copy, Download, FileJson, Send, Sparkles, Upload } from "lucide-react";

import AdminTabs from "@/components/admin/admin-tabs";
import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminPageHeader, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  commitImport,
  downloadJson,
  generateWithClaude,
  getImportBatch,
  getImportGuide,
  getImportSchema,
  getImportStatus,
  listImportBatches,
  LMS_LEVELS,
  publishImportBatch,
  SKILL_KEYS,
  SKILL_LABELS,
  validateImport,
  type ImportBatch,
  type ImportReport,
  type LmsLevel,
  type SkillKey,
} from "@/features/admin/services/lms-service";

import { ImportItemCard, skillLabel } from "./import-preview";

const BATCHES_KEY = ["lms-import-batches"];

function formatDate(iso: string | null) {
  return iso ? new Date(iso).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" }) : "—";
}

// ============================================================
// Claude prompt + format per level
// ============================================================

function GuidePanel() {
  const [level, setLevel] = useState<LmsLevel>("A1");
  const [copied, setCopied] = useState(false);
  const { data: guide, isLoading } = useQuery({ queryKey: ["lms-import-guide", level], queryFn: () => getImportGuide(level) });

  async function copy() {
    if (!guide) return;
    await navigator.clipboard.writeText(guide.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <AdminCard className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-[var(--admin-text-primary)]">Claude-Anweisung pro Niveau</h2>
          <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
            Prompt in Claude einfügen, &lt;MODUL&gt; / &lt;LEKTION&gt; / &lt;THEMA&gt; ersetzen, das JSON zurück hier importieren.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="w-28">
            <AdminSelect value={level} onChange={(e) => setLevel(e.target.value as LmsLevel)} aria-label="Niveau">
              {LMS_LEVELS.map((lv) => (
                <option key={lv} value={lv}>
                  {lv}
                </option>
              ))}
            </AdminSelect>
          </div>
          <AdminButton variant="secondary" onClick={copy} disabled={!guide} data-testid="guide-copy">
            {copied ? <Check size={15} /> : <Copy size={15} />} Prompt kopieren
          </AdminButton>
          <AdminButton variant="secondary" onClick={() => guide && downloadJson(guide.example, `vizu-${level.toLowerCase()}-beispiel.json`)} disabled={!guide}>
            <Download size={15} /> Beispiel
          </AdminButton>
          <AdminButton variant="secondary" onClick={async () => downloadJson(await getImportSchema(), "vizu-lesson-content-1.0.schema.json")}>
            <Download size={15} /> JSON-Schema
          </AdminButton>
        </div>
      </div>
      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {guide && (
        <>
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-xl bg-black/30 p-4 text-xs leading-relaxed text-[var(--admin-text-secondary)]" data-testid="guide-prompt">
            {guide.prompt}
          </pre>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">Prüfliste</p>
              <ul className="space-y-1 text-xs text-[var(--admin-text-secondary)]">
                {guide.checklist.map((c, i) => (
                  <li key={i}>✓ {c}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">Standard-Raster {level}</p>
              <p className="text-xs text-[var(--admin-text-secondary)]">
                <b>Schreiben:</b> {guide.default_rubrics.writing.map((c) => `${c.name} ${c.max}`).join(" · ")}
              </p>
              <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
                <b>Sprechen:</b> {guide.default_rubrics.speaking.map((c) => `${c.name} ${c.max}`).join(" · ")}
              </p>
            </div>
          </div>
        </>
      )}
    </AdminCard>
  );
}

// ============================================================
// Optional server-side generation (only when ANTHROPIC_API_KEY is set)
// ============================================================

function GeneratePanel({ onDocument }: { onDocument: (json: string, report: ImportReport) => void }) {
  const { data: status } = useQuery({ queryKey: ["lms-import-status"], queryFn: getImportStatus });
  const [form, setForm] = useState({ level: "A1" as LmsLevel, module: 1, lesson: 1, topic: "", notes: "", skills: [...SKILL_KEYS] as SkillKey[] });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!status) return <AdminCard><p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p></AdminCard>;
  if (!status.claude_api_configured) {
    return (
      <AdminCard>
        <span data-testid="claude-not-configured" />
        <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Claude-API ist nicht konfiguriert.</p>
        <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">
          Auf dem Server ist kein ANTHROPIC_API_KEY gesetzt. Nutze den Prompt (Tab „Claude-Anweisung“) und importiere das JSON — oder
          bearbeite Inhalte direkt in der Lektion.
        </p>
      </AdminCard>
    );
  }

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const out = await generateWithClaude({ ...form, notes: form.notes.trim() || null });
      onDocument(JSON.stringify(out.document, null, 2), out.report);
    } catch (err) {
      setError(apiErrorMessage(err, "Generierung fehlgeschlagen."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AdminCard className="space-y-4">
      <p className="text-xs text-[var(--admin-text-muted)]">
        Modell: {status.model}. Das Ergebnis ist ein Entwurf: es wird geprüft und erscheint unten in der Vorschau — gespeichert wird erst nach „Als Entwurf anlegen“.
      </p>
      <div className="grid gap-3 sm:grid-cols-4">
        <AdminSelect value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value as LmsLevel })} aria-label="Niveau">
          {LMS_LEVELS.map((lv) => (
            <option key={lv}>{lv}</option>
          ))}
        </AdminSelect>
        <AdminInput type="number" min={1} value={form.module} onChange={(e) => setForm({ ...form, module: Number(e.target.value) })} aria-label="Modul" placeholder="Modul" />
        <AdminInput type="number" min={1} value={form.lesson} onChange={(e) => setForm({ ...form, lesson: Number(e.target.value) })} aria-label="Lektion" placeholder="Lektion" />
        <AdminInput value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })} placeholder="Thema" aria-label="Thema" />
      </div>
      <div className="flex flex-wrap gap-4">
        {SKILL_KEYS.map((k) => (
          <label key={k} className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
            <AdminCheckbox
              checked={form.skills.includes(k)}
              onCheckedChange={(v) => setForm({ ...form, skills: v ? [...form.skills, k] : form.skills.filter((s) => s !== k) })}
              aria-label={SKILL_LABELS[k]}
            />
            {SKILL_LABELS[k]}
          </label>
        ))}
      </div>
      <AdminTextarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Zusätzliche Hinweise (optional)" />
      {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
      <AdminButton onClick={generate} disabled={busy || !form.topic.trim() || !form.skills.length}>
        <Sparkles size={15} /> {busy ? "Claude schreibt… (bis zu 3 Min.)" : "Entwurf generieren"}
      </AdminButton>
    </AdminCard>
  );
}

// ============================================================
// Batches (committed imports) + publish
// ============================================================

function BatchDetail({ batchId, onClose }: { batchId: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const { data: batch } = useQuery({ queryKey: ["lms-import-batch", batchId], queryFn: () => getImportBatch(batchId) });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const created = batch?.items?.filter((i) => i.status === "created") ?? [];
  const unpublished = created.filter((i) => !i.published);

  async function publish() {
    setBusy(true);
    setError(null);
    try {
      const next = await publishImportBatch(batchId);
      queryClient.setQueryData(["lms-import-batch", batchId], next);
      await queryClient.invalidateQueries({ queryKey: BATCHES_KEY });
      await queryClient.invalidateQueries({ queryKey: ["lms-structure"] });
    } catch (err) {
      setError(apiErrorMessage(err, "Veröffentlichen fehlgeschlagen."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <FormDialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={`Import ${batch?.filename ?? ""}`.trim()}
      description={batch ? `${formatDate(batch.created_at)} · ${batch.created_items} angelegt · ${batch.failed_items} fehlerhaft · ${batch.published_items} veröffentlicht` : undefined}
      size="xl"
      footer={
        <>
          <AdminButton variant="ghost" onClick={onClose}>
            Schließen
          </AdminButton>
          <AdminButton onClick={publish} disabled={busy || !unpublished.length} data-testid="batch-publish">
            <Send size={15} /> {busy ? "Wird veröffentlicht..." : `Veröffentlichen (${unpublished.length})`}
          </AdminButton>
        </>
      }
    >
      <div className="space-y-2">
        <p className="text-xs text-[var(--admin-text-muted)]">
          Vor dem Veröffentlichen die Inhalte in der Lektion prüfen (Links). Hören-Aufgaben werden erst veröffentlicht, wenn ihr Audio hochgeladen ist.
        </p>
        {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
        {batch?.items?.map((i) => (
          <div key={i.index} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-white/[0.03] px-3 py-2 text-sm ring-1 ring-[var(--admin-border)]" data-testid="batch-item">
            <div className="min-w-0">
              <p className="font-medium text-[var(--admin-text-primary)]">
                <span className="mr-2 text-xs text-[var(--admin-text-muted)]">
                  {i.level} · {skillLabel(i.skill)}
                </span>
                {i.title}
              </p>
              {i.status === "error" && <p className="text-xs text-[var(--admin-danger)]">{i.errors.join(" · ")}</p>}
              {i.publish_problem === "AUDIO_REQUIRED" && (
                <p className="text-xs text-[var(--admin-warning)]">
                  Audio fehlt{i.audio_hint ? ` (erwartet: ${i.audio_hint})` : ""} — im Hören-Tab hochladen, dann erneut veröffentlichen.
                </p>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs">
              {i.status === "created" ? (
                <span className={i.published ? "font-semibold text-[var(--admin-accent)]" : "text-[var(--admin-text-muted)]"}>
                  {i.published ? "Veröffentlicht" : "Entwurf"}
                </span>
              ) : (
                <span className="font-semibold text-[var(--admin-danger)]">Nicht angelegt</span>
              )}
              {i.lesson_id && (
                <Link
                  href={`/admin/lessons/${i.lesson_id}?tab=${({ lesen: "lesen", hoeren: "hoeren", schreiben: "writing", sprechen: "speaking" } as Record<string, string>)[i.skill ?? ""] ?? "video"}`}
                  className="font-semibold text-[var(--admin-primary)] hover:underline"
                >
                  Lektion öffnen
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>
    </FormDialog>
  );
}

function BatchList({ openBatch }: { openBatch: (id: string) => void }) {
  const { data: batches, isLoading } = useQuery({ queryKey: BATCHES_KEY, queryFn: listImportBatches });
  return (
    <AdminCard className="p-0">
      <div className="border-b border-[var(--admin-border)] px-5 py-3.5">
        <h2 className="font-bold text-[var(--admin-text-primary)]">Importe</h2>
      </div>
      {isLoading && <p className="px-5 py-4 text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {!isLoading && !batches?.length && <p className="px-5 py-4 text-sm text-[var(--admin-text-muted)]">Noch keine Importe.</p>}
      <div className="divide-y divide-[var(--admin-border)]">
        {batches?.map((b: ImportBatch) => (
          <button
            key={b.id}
            type="button"
            onClick={() => openBatch(b.id)}
            className="flex w-full flex-wrap items-center justify-between gap-2 px-5 py-3 text-left text-sm hover:bg-[var(--admin-hover)]"
            data-testid="batch-row"
          >
            <span className="font-medium text-[var(--admin-text-primary)]">
              {b.filename ?? "JSON"} <span className="ml-1 text-xs text-[var(--admin-text-muted)]">{b.levels.join(", ")}</span>
            </span>
            <span className="text-xs text-[var(--admin-text-secondary)]">
              {formatDate(b.created_at)} · {b.created_items} angelegt · {b.failed_items} Fehler ·{" "}
              <b className={b.published_items === b.created_items && b.created_items ? "text-[var(--admin-accent)]" : "text-[var(--admin-warning)]"}>
                {b.published_items}/{b.created_items} veröffentlicht
              </b>
            </span>
          </button>
        ))}
      </div>
    </AdminCard>
  );
}

// ============================================================
// Page
// ============================================================

/** Claude -> JSON -> Validierung -> Vorschau -> Admin legt Entwürfe an ->
 * Prüfung -> Veröffentlichung. Nothing imported is published automatically. */
export default function ContentImportClient() {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [json, setJson] = useState("");
  const [filename, setFilename] = useState<string | null>(null);
  const [createMissing, setCreateMissing] = useState(false);
  const [skipExisting, setSkipExisting] = useState(false);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [checkedJson, setCheckedJson] = useState<string | null>(null);
  const [busy, setBusy] = useState<"validate" | "commit" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openBatch, setOpenBatch] = useState<string | null>(null);
  const [showValidOnly, setShowValidOnly] = useState<"all" | "invalid">("all");

  function parse(): unknown | undefined {
    try {
      return JSON.parse(json);
    } catch (err) {
      setError(`Kein gültiges JSON: ${(err as Error).message}`);
      setReport(null);
      return undefined;
    }
  }

  async function validate() {
    setError(null);
    const doc = parse();
    if (doc === undefined) return;
    setBusy("validate");
    try {
      setReport(await validateImport(doc, createMissing, skipExisting));
      setCheckedJson(json + String(createMissing) + String(skipExisting));
    } catch (err) {
      setError(apiErrorMessage(err, "Prüfung fehlgeschlagen."));
    } finally {
      setBusy(null);
    }
  }

  async function commit() {
    setError(null);
    const doc = parse();
    if (doc === undefined) return;
    setBusy("commit");
    try {
      const batch = await commitImport(doc, filename, createMissing, skipExisting);
      await queryClient.invalidateQueries({ queryKey: BATCHES_KEY });
      await queryClient.invalidateQueries({ queryKey: ["lms-structure"] });
      setReport(null);
      setCheckedJson(null);
      setOpenBatch(batch.id);
    } catch (err) {
      setError(apiErrorMessage(err, "Import fehlgeschlagen."));
    } finally {
      setBusy(null);
    }
  }

  async function readFile(file: File) {
    if (file.size > 5 * 1024 * 1024) {
      setError("Datei ist größer als 5 MB.");
      return;
    }
    setJson(await file.text());
    setFilename(file.name);
    setReport(null);
    setError(null);
  }

  const stale = report !== null && checkedJson !== json + String(createMissing) + String(skipExisting);
  const canCommit = !!report && !stale && report.errors.length === 0 && report.valid > 0;
  const items = report?.items.filter((i) => showValidOnly === "all" || !i.valid) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <Link href="/admin/lms" className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]">
          <ArrowLeft size={14} />
          LMS A1–C1
        </Link>
        <AdminPageHeader
          title="Inhalte importieren"
          description="Claude → JSON → Prüfung → Vorschau → als Entwurf anlegen → prüfen → veröffentlichen. Für alle Niveaus A1–C1."
        />
      </div>

      <AdminTabs
        defaultValue="json"
        tabs={[
          {
            value: "json",
            label: "JSON importieren",
            content: (
              <AdminCard className="space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    ref={fileRef}
                    type="file"
                    accept="application/json,.json"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) void readFile(f);
                      e.target.value = "";
                    }}
                    data-testid="import-file"
                  />
                  <AdminButton variant="secondary" onClick={() => fileRef.current?.click()}>
                    <Upload size={15} /> JSON-Datei wählen
                  </AdminButton>
                  {filename && <span className="text-xs text-[var(--admin-text-muted)]">{filename}</span>}
                </div>
                <AdminTextarea
                  rows={12}
                  value={json}
                  onChange={(e) => {
                    setJson(e.target.value);
                    setFilename(null);
                  }}
                  placeholder='{"schema_version": "1.0", "items": [ … ]}'
                  className="resize-y font-mono text-xs"
                  spellCheck={false}
                  aria-label="JSON"
                  data-testid="import-json"
                />
                <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
                  <AdminCheckbox checked={createMissing} onCheckedChange={setCreateMissing} aria-label="Fehlende Module/Lektionen anlegen" />
                  Fehlende Module / Lektionen anlegen (der Kurs des Niveaus muss existieren)
                </label>
                <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
                  <AdminCheckbox checked={skipExisting} onCheckedChange={setSkipExisting} aria-label="Vorhandenes überspringen" />
                  Erneuter Import: vorhandene Inhalte (gleiche content_id, gleicher Titel, gleiches Wort) überspringen statt Fehler
                </label>
                {error && (
                  <p className="text-sm text-[var(--admin-danger)]" role="alert">
                    {error}
                  </p>
                )}
                <div className="flex flex-wrap gap-2">
                  <AdminButton onClick={validate} disabled={!json.trim() || busy !== null} data-testid="import-validate">
                    <FileJson size={15} /> {busy === "validate" ? "Wird geprüft..." : "Prüfen & Vorschau"}
                  </AdminButton>
                  <AdminButton variant="secondary" onClick={commit} disabled={!canCommit || busy !== null} data-testid="import-commit">
                    {busy === "commit" ? "Wird angelegt..." : `${report?.valid ?? 0} gültige als Entwurf anlegen`}
                  </AdminButton>
                </div>
                {stale && <p className="text-xs text-[var(--admin-warning)]">JSON oder Option geändert — bitte erneut prüfen.</p>}
              </AdminCard>
            ),
          },
          { value: "guide", label: "Claude-Anweisung", content: <GuidePanel /> },
          {
            value: "generate",
            label: "Claude-API",
            content: (
              <GeneratePanel
                onDocument={(text, r) => {
                  setJson(text);
                  setFilename("claude-generated.json");
                  setReport(r);
                  setCheckedJson(text + String(false) + String(skipExisting));
                  setCreateMissing(false);
                }}
              />
            ),
          },
        ]}
      />

      {report && (
        <AdminCard className="space-y-4">
          <span data-testid="import-report" className="hidden" />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-[var(--admin-text-primary)]">Prüfergebnis</h2>
              <p className="mt-1 text-sm text-[var(--admin-text-secondary)]" data-testid="import-summary">
                {report.total} Einträge · <b className="text-[var(--admin-accent)]">{report.valid} gültig</b> ·{" "}
                <b className={report.invalid ? "text-[var(--admin-danger)]" : ""}>{report.invalid} fehlerhaft</b>
                {report.skipped ? <> · {report.skipped} übersprungen</> : null}
              </p>
            </div>
            <div className="w-44">
              <AdminSelect value={showValidOnly} onChange={(e) => setShowValidOnly(e.target.value as "all" | "invalid")} aria-label="Filter">
                <option value="all">Alle anzeigen</option>
                <option value="invalid">Nur fehlerhafte</option>
              </AdminSelect>
            </div>
          </div>
          {report.errors.length > 0 && (
            <ul className="rounded-lg bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]">
              {report.errors.map((e, i) => (
                <li key={i}>• {e}</li>
              ))}
            </ul>
          )}
          <p className="text-xs text-[var(--admin-text-muted)]">
            Fehlerhafte Einträge werden nicht angelegt. Angelegte Inhalte bleiben verborgen, bis du sie veröffentlichst.
          </p>
          <div className="space-y-2.5">
            {items.map((item) => (
              <ImportItemCard key={item.index} item={item} />
            ))}
          </div>
        </AdminCard>
      )}

      <BatchList openBatch={setOpenBatch} />
      {openBatch && <BatchDetail batchId={openBatch} onClose={() => setOpenBatch(null)} />}
    </div>
  );
}
