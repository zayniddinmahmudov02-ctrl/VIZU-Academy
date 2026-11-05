"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Monitor, Smartphone, Upload } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminLabel } from "@/components/admin/admin-ui";
import { API_URL } from "@/constants/api";
import { discardTheme, getAdminThemes, publishTheme, saveThemeDraft, uploadThemeAsset, type AdminTheme, type ThemeDraft } from "@/features/admin/services/battle-admin-service";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import BattleAvatar from "@/features/battle/components/battle-avatar";
import { resolveThemeImage } from "@/features/battle/lib/battle-utils";
import type { Stage } from "@/features/battle/services/battle-service";
import { cn } from "@/lib/utils";

import "@/features/battle/battle.css";

type Editable = Required<Pick<ThemeDraft, "city" | "title" | "accent" | "overlay" | "is_active">> & ThemeDraft;

function merged(t: AdminTheme): Editable {
  const d = t.draft ?? {};
  return {
    city: (d.city as string) ?? t.city, title: (d.title as string) ?? t.title, subtitle: (d.subtitle as string | null) ?? t.subtitle,
    desktop_image: (d.desktop_image as string | null) ?? t.desktop_image, mobile_image: (d.mobile_image as string | null) ?? t.mobile_image,
    accent: (d.accent as string) ?? t.accent, overlay: (d.overlay as number) ?? t.overlay, is_active: (d.is_active as boolean) ?? t.is_active,
    attribution: { ...t.attribution, ...((d.attribution as object) ?? {}) },
  };
}

export default function ThemesPanel() {
  const qc = useQueryClient();
  const themes = useQuery({ queryKey: ["admin-battle-themes"], queryFn: getAdminThemes });
  const [stage, setStage] = useState<Stage>("A1");
  const [form, setForm] = useState<Editable | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const current = themes.data?.find((t) => t.stage === stage);
  const value = form ?? (current && !current.missing ? merged(current) : null);

  const store = (t: AdminTheme) => {
    qc.setQueryData<AdminTheme[]>(["admin-battle-themes"], (old) => old?.map((x) => (x.stage === t.stage ? t : x)));
    setForm(null);
  };
  const onError = (e: unknown) => setMsg(apiErrorMessage(e, "Aktion fehlgeschlagen."));
  const save = useMutation({ mutationFn: () => saveThemeDraft(stage, value!), onSuccess: (t) => { store(t); setMsg("Entwurf gespeichert — prüfe die Vorschau, dann veröffentlichen."); }, onError });
  const publish = useMutation({ mutationFn: () => publishTheme(stage), onSuccess: (t) => { store(t); setMsg(`Theme ${stage} veröffentlicht.`); }, onError });
  const discard = useMutation({ mutationFn: () => discardTheme(stage), onSuccess: (t) => { store(t); setMsg("Entwurf verworfen."); }, onError });
  const upload = useMutation({
    mutationFn: ({ kind, file }: { kind: "desktop" | "mobile"; file: File }) => uploadThemeAsset(kind, file),
    onSuccess: (r, v) => { setForm({ ...value!, [v.kind === "desktop" ? "desktop_image" : "mobile_image"]: r.ref }); setMsg(`Bild hochgeladen (${r.width}×${r.height}, ${Math.round(r.size_bytes / 1024)} KB) — Entwurf speichern nicht vergessen.`); },
    onError,
  });

  if (themes.isLoading) return <AdminCard><p className="text-sm text-[var(--admin-text-secondary)]">Lädt…</p></AdminCard>;
  if (themes.isError || !themes.data) return <AdminCard><p className="text-sm text-[var(--admin-danger)]">Themes konnten nicht geladen werden.</p></AdminCard>;

  const set = (patch: Partial<Editable>) => setForm({ ...value!, ...patch });
  const busy = save.isPending || publish.isPending || discard.isPending || upload.isPending;

  return (
    <div className="space-y-4" data-testid="admin-battle-themes">
      <div className="flex flex-wrap gap-2">
        {themes.data.map((t) => (
          <button key={t.stage} type="button" onClick={() => { setStage(t.stage); setForm(null); setMsg(null); }} data-testid={`admin-theme-${t.stage}`}
                  className={cn("rounded-xl px-4 py-2 text-sm font-semibold ring-1", stage === t.stage ? "bg-[var(--admin-primary)] text-white ring-transparent" : "bg-[var(--admin-card)] text-[var(--admin-text-primary)] ring-[var(--admin-border)]")}>
            {t.stage} {t.missing ? "· fehlt" : `· ${t.city}`}{t.draft && <span className="ml-1 text-amber-300">●</span>}
          </button>
        ))}
      </div>
      {msg && <p role="status" className="text-sm text-amber-300">{msg}</p>}

      {!value ? <AdminCard><p className="text-sm text-[var(--admin-text-secondary)]">Theme fehlt — zuerst <code>python -m app.scripts.battle_seed</code> ausführen.</p></AdminCard> : (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,420px)_1fr]">
          <AdminCard className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div><AdminLabel>Stadt</AdminLabel><AdminInput value={value.city} onChange={(e) => set({ city: e.target.value })} /></div>
              <div><AdminLabel>Titel</AdminLabel><AdminInput value={value.title} onChange={(e) => set({ title: e.target.value })} /></div>
            </div>
            <div><AdminLabel>Untertitel</AdminLabel><AdminInput value={value.subtitle ?? ""} onChange={(e) => set({ subtitle: e.target.value })} /></div>
            {(["desktop", "mobile"] as const).map((kind) => {
              const key = kind === "desktop" ? "desktop_image" : "mobile_image";
              return (
                <div key={kind}>
                  <AdminLabel>{kind === "desktop" ? "Desktop-Hintergrund (16:9)" : "Mobile-Hintergrund (9:16)"}</AdminLabel>
                  <div className="flex gap-2">
                    <AdminInput value={value[key] ?? ""} onChange={(e) => set({ [key]: e.target.value })} className="font-mono text-xs" />
                    <label className="inline-flex h-10 shrink-0 cursor-pointer items-center gap-1.5 rounded-lg bg-[var(--admin-card)] px-3 text-xs font-semibold text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)]">
                      <Upload size={14} /> Datei
                      <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(e) => { const f = e.target.files?.[0]; if (f) upload.mutate({ kind, file: f }); }} />
                    </label>
                  </div>
                </div>
              );
            })}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <AdminLabel>Akzentfarbe</AdminLabel>
                <div className="flex items-center gap-2">
                  <input type="color" value={value.accent} onChange={(e) => set({ accent: e.target.value.toUpperCase() })} className="h-10 w-12 rounded" aria-label="Akzentfarbe" />
                  <AdminInput value={value.accent} onChange={(e) => set({ accent: e.target.value })} className="font-mono" />
                </div>
              </div>
              <div>
                <AdminLabel>Overlay {value.overlay}%</AdminLabel>
                <input type="range" min={0} max={90} value={value.overlay} onChange={(e) => set({ overlay: Number(e.target.value) })} className="mt-3 w-full" aria-label="Overlay" />
              </div>
            </div>
            <fieldset className="space-y-2 rounded-xl p-3 ring-1 ring-[var(--admin-border)]">
              <legend className="px-1 text-xs font-semibold text-[var(--admin-text-secondary)]">Bildnachweis (Pflicht für Veröffentlichung)</legend>
              {(["author", "license", "license_url", "source_url", "title"] as const).map((k) => (
                <AdminInput key={k} placeholder={{ author: "Autor *", license: "Lizenz *", license_url: "Lizenz-URL", source_url: "Quelle (URL)", title: "Dateititel" }[k]}
                            value={value.attribution?.[k] ?? ""} onChange={(e) => set({ attribution: { ...value.attribution, [k]: e.target.value } })} />
              ))}
            </fieldset>
            <label className="flex items-center gap-2 text-sm text-[var(--admin-text-primary)]">
              <AdminCheckbox checked={value.is_active} onCheckedChange={(v) => set({ is_active: !!v })} /> Aktiv (sonst Standard-Theme)
            </label>
            <div className="flex flex-wrap gap-2 pt-1">
              <AdminButton variant="secondary" disabled={busy} onClick={() => save.mutate()} data-testid="admin-theme-save">Entwurf speichern</AdminButton>
              <AdminButton disabled={busy || !current?.draft || !!form} onClick={() => publish.mutate()} data-testid="admin-theme-publish" title={form ? "Erst Entwurf speichern" : undefined}>Veröffentlichen</AdminButton>
              {current?.draft && <AdminButton variant="ghost" disabled={busy} onClick={() => discard.mutate()}>Entwurf verwerfen</AdminButton>}
            </div>
            <p className="text-[11px] text-[var(--admin-text-muted)]">Live seit: {current?.published_at ? new Date(current.published_at).toLocaleString("de-DE") : "—"}. Spieler sehen erst nach „Veröffentlichen“ die Änderungen.</p>
          </AdminCard>

          <div className="space-y-3">
            <p className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]"><Monitor size={15} /> Vorschau Desktop</p>
            <Preview theme={value} stage={stage} mode="desktop" />
            <p className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]"><Smartphone size={15} /> Vorschau Mobile</p>
            <Preview theme={value} stage={stage} mode="mobile" />
          </div>
        </div>
      )}
    </div>
  );
}

function Preview({ theme, stage, mode }: { theme: Editable; stage: Stage; mode: "desktop" | "mobile" }) {
  const src = resolveThemeImage(mode === "desktop" ? theme.desktop_image : theme.mobile_image ?? theme.desktop_image, API_URL);
  const o = theme.overlay / 100;
  const mobile = mode === "mobile";
  return (
    <div className={cn("battle-root relative overflow-hidden rounded-2xl ring-1 ring-[var(--admin-border)]", mobile ? "aspect-[9/16] w-[260px]" : "aspect-video w-full")} style={{ minHeight: 0 }}
         data-testid={`admin-theme-preview-${mode}`}>
      {/* eslint-disable-next-line @next/next/no-img-element -- preview of the theme picture */}
      {src ? <img src={src} alt="" className="absolute inset-0 h-full w-full object-cover" /> : <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,#1f4e9a,#101d35)]" />}
      <div className="absolute inset-0" style={{ background: `linear-gradient(180deg, rgba(16,29,53,${o * 0.55}) 0%, rgba(16,29,53,${o * 0.35}) 35%, rgba(16,29,53,${Math.min(0.97, o + 0.35)}) 100%)` }} />
      <div className="bt-flag-line absolute inset-x-0 top-0 h-[3px]" />
      <div className={cn("relative flex h-full", mobile ? "flex-col items-center justify-end gap-2 p-3 pb-4" : "items-center gap-6 p-6")}>
        <div className={cn(mobile ? "text-center" : "flex-1")}>
          <span className="inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-black ring-1" style={{ background: `${theme.accent}33`, borderColor: theme.accent, color: "#fff" }}>
            <span className="text-[#F2C45B]">{stage}</span>&nbsp;· {theme.city}
          </span>
          <p className={cn("bt-display mt-2", mobile ? "text-2xl" : "text-4xl")}>VIZU <span style={{ color: theme.accent }}>DEUTSCH</span><br /><span className="bt-gold-text">BATTLE</span></p>
          <p className={cn("mt-1 font-semibold text-white/85", mobile ? "text-[10px]" : "text-sm")}>{theme.subtitle || theme.title}</p>
          <span className={cn("bt-btn-start mt-3 inline-flex items-center rounded-xl font-black uppercase", mobile ? "px-3 py-1.5 text-[10px]" : "px-5 py-2.5 text-xs")}>Battle starten</span>
        </div>
        <div className={cn("bt-card-light rounded-2xl p-2", mobile ? "w-full" : "w-[38%]")}>
          <div className="grid aspect-[4/3] place-items-center rounded-xl bg-[#e9eef6]"><BattleAvatar avatar="student" size={mobile ? 70 : 90} accent={theme.accent} animated={false} /></div>
          <p className="my-1.5 text-center text-[11px] font-black">Wie heißt das auf Deutsch?</p>
          <div className="grid grid-cols-2 gap-1">
            {["der Apfel", "die Banane", "das Brot", "der Käse"].map((x, i) => (
              <span key={x} className={cn("rounded-lg px-2 py-1 text-[10px] font-bold ring-1", i === 0 ? "text-white" : "bg-white ring-[#dfe5f0]")} style={i === 0 ? { background: theme.accent } : undefined}>{x}</span>
            ))}
          </div>
        </div>
      </div>
      {theme.attribution?.author && <p className="absolute bottom-1 right-2 max-w-[90%] truncate text-[9px] text-white/60">Foto: {theme.attribution.author} · {theme.attribution.license}</p>}
    </div>
  );
}
