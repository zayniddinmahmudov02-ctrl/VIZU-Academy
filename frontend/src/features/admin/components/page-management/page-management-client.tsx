"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Archive,
  Eye,
  EyeOff,
  FileText,
  History,
  LoaderCircle,
  RotateCcw,
  Search,
  Shield,
  Trash2,
} from "lucide-react";

import { AdminButton, AdminInput, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  archiveManagedPage,
  getManagedPageDetails,
  getManagedPageHistory,
  listManagedPages,
  restoreManagedPage,
  setManagedPageNavigation,
  setManagedPageVisibility,
  type ManagedPage,
  type ManagedPageAudit,
  type ManagedPageStatus,
} from "@/features/admin/services/page-management-service";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";

const statusStyle: Record<ManagedPageStatus, string> = {
  active: "bg-[var(--admin-success)]/10 text-[var(--admin-success)]",
  removed: "bg-[var(--admin-warning)]/10 text-[var(--admin-warning)]",
  hidden: "bg-[var(--admin-warning)]/10 text-[var(--admin-warning)]",
  archived: "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]",
};

const statusLabel: Record<ManagedPageStatus, string> = {
  active: "Faol",
  removed: "Navigatsiyadan olingan",
  hidden: "Yashirilgan",
  archived: "Arxivlangan",
};

const actionLabel: Record<string, string> = {
  navigation: "Navigatsiya o‘zgartirildi",
  visibility: "Ko‘rinish o‘zgartirildi",
  archive: "Sahifa arxivlandi",
  restore: "Sahifa tiklandi",
};

function dateLabel(value: string | null) {
  return value ? new Date(value).toLocaleString("de-DE") : "—";
}

function StateBadge({ status }: { status: ManagedPageStatus }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyle[status]}`}>{statusLabel[status]}</span>;
}

export default function PageManagementClient() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [routeSearch, setRouteSearch] = useState("");
  const [moduleFilter, setModuleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<ManagedPageStatus | "">("");
  const [confirmPage, setConfirmPage] = useState<{ page: ManagedPage; action: "archive" | "restore" } | null>(null);
  const [detailsPage, setDetailsPage] = useState<ManagedPage | null>(null);
  const [historyPage, setHistoryPage] = useState<ManagedPage | null>(null);
  const [reason, setReason] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const pagesQuery = useQuery({
    queryKey: ["admin-managed-pages"],
    queryFn: () => listManagedPages(),
  });
  const historyQuery = useQuery({
    queryKey: ["admin-managed-page-history", historyPage?.page_id],
    queryFn: () => getManagedPageHistory(historyPage!.page_id),
    enabled: Boolean(historyPage),
  });
  const detailsQuery = useQuery({
    queryKey: ["admin-managed-page-details", detailsPage?.page_id],
    queryFn: () => getManagedPageDetails(detailsPage!.page_id),
    enabled: Boolean(detailsPage),
  });

  const modules = useMemo(
    () => [...new Set((pagesQuery.data ?? []).map((page) => page.module))].sort((a, b) => a.localeCompare(b)),
    [pagesQuery.data],
  );
  const pages = useMemo(() => {
    const q = search.trim().toLocaleLowerCase();
    const route = routeSearch.trim().toLocaleLowerCase();
    return (pagesQuery.data ?? []).filter((page) =>
      (!q || `${page.name} ${page.route} ${page.module} ${page.component}`.toLocaleLowerCase().includes(q))
      && (!route || page.route.toLocaleLowerCase().includes(route))
      && (!moduleFilter || page.module === moduleFilter)
      && (!statusFilter || page.status === statusFilter),
    );
  }, [pagesQuery.data, search, routeSearch, moduleFilter, statusFilter]);

  const mutation = useMutation({
    mutationFn: async ({ page, action }: { page: ManagedPage; action: "navigation-off" | "navigation-on" | "hide" | "show" | "archive" | "restore" }) => {
      if (action === "navigation-off" || action === "navigation-on") {
        await setManagedPageNavigation(page.page_id, action === "navigation-on", reason);
      } else if (action === "hide" || action === "show") {
        await setManagedPageVisibility(page.page_id, action === "hide", reason);
      } else if (action === "archive") {
        await archiveManagedPage(page.page_id, reason);
      } else {
        await restoreManagedPage(page.page_id, reason);
      }
    },
    onSuccess: async () => {
      setActionError(null);
      setConfirmPage(null);
      setReason("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin-managed-pages"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-managed-page-navigation"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-managed-page-history"] }),
      ]);
    },
    onError: (error) => setActionError(apiErrorMessage(error, "Sahifa holatini o‘zgartirib bo‘lmadi.")),
  });

  function requestAction(page: ManagedPage, action: "archive" | "restore") {
    setActionError(null);
    setReason("");
    setConfirmPage({ page, action });
  }

  return (
    <div className="space-y-5">
      <AdminPageHeader
        title="Page Management / Seitenverwaltung"
        description="Kod bilan boshqariladigan sahifalar navigatsiyasi va holatini boshqaring. O‘zgarishlar route kodini ham, sahifa ma’lumotlarini ham o‘chirmaydi."
      />

      <section className="rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <label className="relative">
            <span className="sr-only">Sahifa nomi yoki modul bo‘yicha qidirish</span>
            <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
            <AdminInput className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Sahifa nomi, modul…" />
          </label>
          <label>
            <span className="sr-only">Route bo‘yicha qidirish</span>
            <AdminInput value={routeSearch} onChange={(event) => setRouteSearch(event.target.value)} placeholder="Route bo‘yicha qidirish…" />
          </label>
          <AdminSelect value={moduleFilter} onChange={(event) => setModuleFilter(event.target.value)} aria-label="Modul bo‘yicha filter">
            <option value="">Barcha modullar</option>
            {modules.map((module) => <option key={module} value={module}>{module}</option>)}
          </AdminSelect>
          <AdminSelect value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as ManagedPageStatus | "")} aria-label="Holat bo‘yicha filter">
            <option value="">Barcha holatlar</option>
            <option value="active">Faol</option>
            <option value="removed">Navigatsiyadan olingan</option>
            <option value="hidden">Yashirilgan</option>
            <option value="archived">Arxivlangan</option>
          </AdminSelect>
        </div>
        <p className="mt-3 text-xs text-[var(--admin-text-muted)]" aria-live="polite">
          {pages.length} / {pagesQuery.data?.length ?? 0} sahifa
        </p>
      </section>

      {pagesQuery.isPending ? (
        <div role="status" className="flex justify-center py-16">
          <LoaderCircle className="animate-spin text-[var(--admin-primary)]" size={28} />
          <span className="sr-only">Sahifalar yuklanmoqda</span>
        </div>
      ) : pagesQuery.isError ? (
        <section className="rounded-2xl bg-[var(--admin-card)] p-5 ring-1 ring-[var(--admin-border)]">
          <p role="alert" className="text-sm text-[var(--admin-danger)]">Sahifalar ro‘yxatini yuklab bo‘lmadi.</p>
          <AdminButton className="mt-3" size="sm" variant="secondary" onClick={() => void pagesQuery.refetch()}>Qayta urinish</AdminButton>
        </section>
      ) : pages.length === 0 ? (
        <section className="rounded-2xl bg-[var(--admin-card)] p-8 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
          Filtrga mos sahifa topilmadi.
        </section>
      ) : (
        <section className="overflow-hidden rounded-2xl bg-[var(--admin-card)] ring-1 ring-[var(--admin-border)]">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1280px] text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--admin-border)] bg-white/[0.02]">
                  {["Sahifa / route", "Modul / turi", "Holati", "Ruxsat etilgan rollar", "Navigatsiya", "Komponent", "Bog‘langan yozuvlar", "Oxirgi o‘zgarish", "Amallar"].map((label) => (
                    <th key={label} className="px-3 py-3 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pages.map((page) => (
                  <tr key={page.page_id} className="border-b border-[var(--admin-border)] align-top last:border-0 hover:bg-white/[0.02]">
                    <td className="max-w-64 px-3 py-3">
                      <p className="font-semibold text-[var(--admin-text-primary)]">{page.name}</p>
                      <code className="mt-1 block break-all text-xs text-[var(--admin-text-muted)]">{page.route}</code>
                    </td>
                    <td className="px-3 py-3">
                      <p>{page.module}</p>
                      <p className="mt-1 text-xs text-[var(--admin-text-muted)]">{page.page_type.replace("_", " ")}</p>
                    </td>
                    <td className="px-3 py-3"><StateBadge status={page.status} /></td>
                    <td className="px-3 py-3">{page.allowed_roles.join(", ")}</td>
                    <td className="px-3 py-3">
                      {page.in_navigation
                        ? page.navigation_visible ? "Ko‘rinadi" : "Yashirilgan"
                        : "Menyuda yo‘q"}
                    </td>
                    <td className="max-w-56 px-3 py-3">
                      <code className="break-all text-xs text-[var(--admin-text-secondary)]">{page.component}</code>
                    </td>
                    <td className="px-3 py-3">
                      <details>
                        <summary className="cursor-pointer font-semibold">{page.related_data_exists ? "Bog‘langan ma’lumot bor" : "Bog‘langan ma’lumot topilmadi"}</summary>
                        <ul className="mt-2 space-y-1 text-xs text-[var(--admin-text-muted)]">
                          {page.related_data.map((item) => <li key={item.name}>{item.name}: {item.exists ? "mavjud" : "yo‘q"}</li>)}
                        </ul>
                        <p className="mt-2 max-w-56 text-xs text-[var(--admin-text-muted)]">Bu modul jadvallaridagi mavjudlik tekshiruvi. Navigatsiya amallari ma’lumotlarni o‘zgartirmaydi.</p>
                      </details>
                    </td>
                    <td className="px-3 py-3 text-xs text-[var(--admin-text-secondary)]">
                      <p>{dateLabel(page.updated_at)}</p>
                      <p>{page.updated_by?.name ?? "—"}</p>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex max-w-80 flex-wrap gap-1.5">
                        <AdminButton size="sm" variant="ghost" onClick={() => setDetailsPage(page)}>
                          <FileText size={13} /> Tafsilot
                        </AdminButton>
                        {page.in_navigation && (
                          <AdminButton
                            size="sm"
                            variant="secondary"
                            disabled={mutation.isPending || page.protected}
                            title={page.protected ? "System page himoyalangan" : undefined}
                            onClick={() => mutation.mutate({ page, action: page.navigation_enabled ? "navigation-off" : "navigation-on" })}
                          >
                            {page.navigation_enabled ? "Menudan olish" : "Menyuga qaytarish"}
                          </AdminButton>
                        )}
                        <AdminButton
                          size="sm"
                          variant="secondary"
                          disabled={mutation.isPending || page.protected}
                          title={page.protected ? "System page himoyalangan" : undefined}
                          onClick={() => mutation.mutate({ page, action: page.is_hidden ? "show" : "hide" })}
                        >
                          {page.is_hidden ? <Eye size={13} /> : <EyeOff size={13} />}
                          {page.is_hidden ? "Ko‘rsatish" : "Yashirish"}
                        </AdminButton>
                        {page.is_archived ? (
                          <AdminButton size="sm" variant="secondary" disabled={mutation.isPending} onClick={() => requestAction(page, "restore")}>
                            <RotateCcw size={13} /> Tiklash
                          </AdminButton>
                        ) : (
                          <AdminButton
                            size="sm"
                            variant="secondary"
                            disabled={mutation.isPending || page.protected}
                            title={page.protected ? "System page himoyalangan" : undefined}
                            onClick={() => requestAction(page, "archive")}
                          >
                            <Archive size={13} /> Arxivlash
                          </AdminButton>
                        )}
                        <AdminButton size="sm" variant="ghost" onClick={() => setHistoryPage(page)} aria-label={`${page.name} audit tarixini ko‘rish`}>
                          <History size={13} /> Tarix
                        </AdminButton>
                        <AdminButton size="sm" variant="danger" disabled title={page.delete_block_reason}>
                          <Trash2 size={13} /> O‘chirish mumkin emas
                        </AdminButton>
                        {page.protected && <span className="inline-flex items-center gap-1 self-center text-xs text-[var(--admin-text-muted)]"><Shield size={12} /> Himoyalangan</span>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {actionError && <p role="alert" className="text-sm text-[var(--admin-danger)]">{actionError}</p>}

      <ConfirmDialog
        open={Boolean(confirmPage)}
        onOpenChange={(open) => { if (!open && !mutation.isPending) setConfirmPage(null); }}
        title={confirmPage?.action === "archive" ? "Sahifani arxivlash" : "Sahifani tiklash"}
        description={confirmPage?.action === "archive"
          ? `${confirmPage.page.name} navigatsiyadan olinadi va arxivlanadi. Route kodi hamda bog‘langan ma’lumotlar saqlanadi.`
          : `${confirmPage?.page.name} arxivdan tiklanadi. Avvalgi navigatsiya sozlamalari saqlangan holda qaytariladi.`}
        confirmLabel={confirmPage?.action === "archive" ? "Arxivlash" : "Tiklash"}
        pendingLabel={mutation.isPending ? "Saqlanmoqda…" : undefined}
        variant={confirmPage?.action === "archive" ? "danger" : "primary"}
        isPending={mutation.isPending}
        error={actionError}
        onConfirm={() => {
          if (confirmPage) mutation.mutate({ page: confirmPage.page, action: confirmPage.action });
        }}
      />

      <HistoryDialog
        page={historyPage}
        entries={historyQuery.data}
        loading={historyQuery.isPending}
        error={historyQuery.isError ? "Audit tarixi yuklanmadi." : null}
        onClose={() => setHistoryPage(null)}
      />
      <PageDetailsDialog
        page={detailsQuery.data ?? detailsPage}
        loading={detailsQuery.isPending}
        error={detailsQuery.isError ? "Sahifa tafsilotlarini yuklab bo‘lmadi." : null}
        onClose={() => setDetailsPage(null)}
      />
    </div>
  );
}

function PageDetailsDialog({
  page,
  loading,
  error,
  onClose,
}: {
  page: ManagedPage | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}) {
  return (
    <FormDialog open={Boolean(page)} onOpenChange={(open) => { if (!open) onClose(); }} title={`Sahifa tafsilotlari: ${page?.name ?? ""}`} description={page?.route} size="lg">
      {loading ? (
        <p role="status" className="py-8 text-center text-sm text-[var(--admin-text-muted)]">Tafsilotlar yuklanmoqda…</p>
      ) : error ? (
        <p role="alert" className="text-sm text-[var(--admin-danger)]">{error}</p>
      ) : page && (
        <dl className="grid gap-3 sm:grid-cols-2">
          <Detail label="Modul" value={page.module} />
          <Detail label="Sahifa turi" value={page.page_type} />
          <Detail label="Holati" value={statusLabel[page.status]} />
          <Detail label="Ruxsat etilgan rollar" value={page.allowed_roles.join(", ")} />
          <Detail label="Sidebar holati" value={page.navigation_visible ? "Ko‘rinadi" : "Ko‘rinmaydi"} />
          <Detail label="Route komponenti" value={page.component} />
          <Detail label="Oxirgi o‘zgarish" value={`${dateLabel(page.updated_at)} · ${page.updated_by?.name ?? "—"}`} />
          <Detail label="Bog‘langan modul ma’lumoti" value={page.related_data_exists ? "Mavjud" : "Topilmadi"} />
          <div className="sm:col-span-2">
            <p className="text-xs font-semibold uppercase text-[var(--admin-text-muted)]">Bog‘langan ma’lumotlar</p>
            <ul className="mt-2 grid gap-1 text-sm text-[var(--admin-text-secondary)] sm:grid-cols-2">
              {page.related_data.map((item) => <li key={item.name}>{item.name}: {item.exists ? "mavjud" : "yo‘q"}</li>)}
            </ul>
            <p className="mt-2 text-xs text-[var(--admin-text-muted)]">Bu modul jadvallari bo‘yicha mavjudlik holati; sahifani yashirish, menyudan olish yoki arxivlash ma’lumotlarni o‘zgartirmaydi.</p>
          </div>
          <div className="rounded-lg bg-[var(--admin-warning)]/10 p-3 text-sm text-[var(--admin-warning)] sm:col-span-2">
            <p className="font-semibold">Butunlay o‘chirish mumkin emas</p>
            <p className="mt-1 text-xs">{page.delete_block_reason}</p>
          </div>
        </dl>
      )}
      <div className="mt-5 flex justify-end">
        <AdminButton variant="secondary" onClick={onClose}>Yopish</AdminButton>
      </div>
    </FormDialog>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg border border-[var(--admin-border)] p-3">
      <dt className="text-xs font-semibold uppercase text-[var(--admin-text-muted)]">{label}</dt>
      <dd className="mt-1 break-all text-sm text-[var(--admin-text-primary)]">{value}</dd>
    </div>
  );
}

function HistoryDialog({
  page,
  entries,
  loading,
  error,
  onClose,
}: {
  page: ManagedPage | null;
  entries: ManagedPageAudit[] | undefined;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}) {
  return (
    <FormDialog open={Boolean(page)} onOpenChange={(open) => { if (!open) onClose(); }} title={`Audit: ${page?.name ?? ""}`} description={page?.route} size="lg">
      {loading ? (
        <p role="status" className="py-8 text-center text-sm text-[var(--admin-text-muted)]">Tarix yuklanmoqda…</p>
      ) : error ? (
        <p role="alert" className="text-sm text-[var(--admin-danger)]">{error}</p>
      ) : !entries?.length ? (
        <p className="py-8 text-center text-sm text-[var(--admin-text-muted)]">Bu sahifa uchun hali boshqaruv amallari yo‘q.</p>
      ) : (
        <ol className="max-h-[60vh] space-y-3 overflow-y-auto">
          {entries.map((entry) => (
            <li key={entry.id} className="rounded-xl border border-[var(--admin-border)] p-3">
              <div className="flex flex-wrap justify-between gap-2">
                <span className="font-semibold text-[var(--admin-text-primary)]">{actionLabel[entry.action] ?? entry.action}</span>
                <time className="text-xs text-[var(--admin-text-muted)]">{dateLabel(entry.created_at)}</time>
              </div>
              <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">Bajargan: {entry.actor?.name ?? "Hisob mavjud emas"}</p>
              <pre className="mt-2 overflow-x-auto rounded-lg bg-black/10 p-2 text-xs text-[var(--admin-text-muted)]">
                {JSON.stringify({ old: entry.previous_state, new: entry.new_state }, null, 2)}
              </pre>
              {entry.reason && <p className="mt-2 text-xs text-[var(--admin-text-secondary)]">Izoh: {entry.reason}</p>}
            </li>
          ))}
        </ol>
      )}
      <div className="mt-5 flex justify-end">
        <AdminButton variant="secondary" onClick={onClose}>Yopish</AdminButton>
      </div>
    </FormDialog>
  );
}
