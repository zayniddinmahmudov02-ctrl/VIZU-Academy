"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BarChart3,
  Globe,
  Pencil,
  Plus,
  Settings,
  ShieldCheck,
  ShieldOff,
  Trash2,
  Users,
} from "lucide-react";

import { AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import {
  languageManagementApi,
} from "@/features/admin/services/language-management-service";
import type { Language } from "@/features/admin/types/language.types";

export default function LanguagesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["languages"],
    queryFn: () => languageManagementApi.list(),
  });

  const [deleting, setDeleting] = useState<Language | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deletePending, setDeletePending] = useState(false);

  async function toggleActive(language: Language) {
    await languageManagementApi.update(language.id, { is_active: !language.is_active });
    queryClient.invalidateQueries({ queryKey: ["languages"] });
  }

  async function handleDelete() {
    if (!deleting) return;
    setDeletePending(true);
    setDeleteError(null);
    try {
      await languageManagementApi.remove(deleting.id);
      queryClient.invalidateQueries({ queryKey: ["languages"] });
      setDeleting(null);
    } catch (err) {
      const message =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Löschen fehlgeschlagen.";
      setDeleteError(message);
    } finally {
      setDeletePending(false);
    }
  }

  const columns: DataTableColumn<Language>[] = [
    {
      key: "flag",
      header: "",
      className: "w-12",
      render: (item) =>
        item.flag_file ? (
          <img src={`/flags/${item.flag_file}`} alt={item.code} className="h-5 w-8 rounded object-cover" />
        ) : (
          <Globe size={18} className="text-[var(--admin-text-muted)]" />
        ),
    },
    {
      key: "name",
      header: "Name",
      render: (item) => (
        <Link
          href={`/admin/languages/${item.id}/dashboard`}
          className="font-medium text-[var(--admin-text-primary)] hover:text-[var(--admin-primary)]"
        >
          {item.name}
          {item.is_default && (
            <span className="ml-2 rounded-full bg-[var(--admin-primary)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-primary)]">
              Standard
            </span>
          )}
        </Link>
      ),
    },
    { key: "code", header: "Code", render: (item) => item.code },
    { key: "locale", header: "Locale", render: (item) => item.locale },
    { key: "learners", header: "Learners", render: (item) => item.learners_count },
    { key: "levels", header: "Levels", render: (item) => item.levels_count },
    { key: "modules", header: "Modules", render: (item) => item.modules_count },
    { key: "lessons", header: "Lessons", render: (item) => item.lessons_count },
    {
      key: "status",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            item.is_active
              ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
              : "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.is_active ? "Aktiv" : "Inaktiv"}
        </span>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (item) => (
        <div className="flex items-center justify-end gap-1">
          <button
            onClick={() => router.push(`/admin/languages/${item.id}/edit`)}
            title="Edit"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-primary)]/10 hover:text-[var(--admin-primary)]"
          >
            <Pencil size={15} />
          </button>
          <button
            onClick={() => router.push(`/admin/languages/${item.id}/dashboard`)}
            title="Statistics"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-primary)]/10 hover:text-[var(--admin-primary)]"
          >
            <BarChart3 size={15} />
          </button>
          <button
            onClick={() => router.push(`/admin/languages/${item.id}/learners`)}
            title="Learners"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-primary)]/10 hover:text-[var(--admin-primary)]"
          >
            <Users size={15} />
          </button>
          <button
            onClick={() => router.push(`/admin/languages/${item.id}/settings`)}
            title="Settings"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-primary)]/10 hover:text-[var(--admin-primary)]"
          >
            <Settings size={15} />
          </button>
          <button
            onClick={() => toggleActive(item)}
            title={item.is_active ? "Deactivate" : "Activate"}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-primary)]/10 hover:text-[var(--admin-primary)]"
          >
            {item.is_active ? <ShieldOff size={15} /> : <ShieldCheck size={15} />}
          </button>
          <button
            onClick={() => {
              setDeleteError(null);
              setDeleting(item);
            }}
            title="Delete"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
          >
            <Trash2 size={15} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader
        title="Languages"
        description="Sprachen, die auf der Plattform unterrichtet werden."
        action={
          <Link href="/admin/languages/new">
            <button className="inline-flex h-10 items-center gap-2 rounded-lg bg-[var(--admin-primary)] px-4 text-sm font-semibold text-white shadow-[0_1px_1px_rgba(0,0,0,0.15),0_8px_16px_-8px_rgba(91,91,248,0.5)] transition-all hover:bg-[var(--admin-primary-hover)]">
              <Plus size={16} />
              Neue Sprache
            </button>
          </Link>
        }
      />

      {isError && (
        <AdminCard className="mb-6">
          <p className="text-sm text-[var(--admin-danger)]">Sprachen konnten nicht geladen werden.</p>
        </AdminCard>
      )}

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage="Noch keine Sprachen angelegt."
      />

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Sprache löschen"
        description={
          deleteError ??
          `"${deleting?.name}" wird deaktiviert und aus der Liste entfernt. Nur möglich, wenn keine Lerner, Levels oder Module existieren.`
        }
        isPending={deletePending}
        onConfirm={handleDelete}
      />
    </div>
  );
}
