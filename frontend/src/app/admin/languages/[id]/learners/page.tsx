"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronLeft, ChevronRight, Search, Star } from "lucide-react";

import { AdminCard, AdminInput, AdminPageHeader } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import {
  getLanguage,
  getLanguageLearners,
} from "@/features/admin/services/language-management-service";
import type { LanguageLearnerItem } from "@/features/admin/types/language.types";

export default function LanguageLearnersPage() {
  const { id } = useParams<{ id: string }>();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data: language } = useQuery({ queryKey: ["language", id], queryFn: () => getLanguage(id) });
  const { data, isLoading } = useQuery({
    queryKey: ["language-learners", id, search, page],
    queryFn: () => getLanguageLearners(id, { search: search || undefined, page, page_size: 20 }),
  });

  const columns: DataTableColumn<LanguageLearnerItem>[] = [
    { key: "username", header: "Nutzername", render: (item) => item.username },
    { key: "email", header: "E-Mail", render: (item) => item.email },
    {
      key: "is_primary",
      header: "Primär",
      render: (item) =>
        item.is_primary ? <Star size={14} className="fill-[var(--admin-primary)] text-[var(--admin-primary)]" /> : "—",
    },
    {
      key: "joined_at",
      header: "Beigetreten",
      render: (item) => new Date(item.joined_at).toLocaleDateString("de-DE"),
    },
    {
      key: "last_activity",
      header: "Letzte Aktivität",
      render: (item) => (item.last_activity ? new Date(item.last_activity).toLocaleString("de-DE") : "—"),
    },
  ];

  return (
    <div>
      <Link
        href="/admin/languages"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Languages
      </Link>

      <AdminPageHeader title={`Learners — ${language?.name ?? ""}`} description="Alle Lerner dieser Sprache." />

      <div className="relative mb-6 max-w-sm">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
        <AdminInput
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="Nach Nutzername oder E-Mail suchen..."
          className="pl-9"
        />
      </div>

      <DataTable
        columns={columns}
        data={data?.items}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage="Keine Lerner gefunden."
      />

      {data && data.total_pages > 1 && (
        <AdminCard className="mt-4 flex items-center justify-between py-3">
          <p className="text-xs text-[var(--admin-text-muted)]">
            Seite {data.page} von {data.total_pages} ({data.total} Lerner)
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-white/5 disabled:opacity-30"
            >
              <ChevronLeft size={15} />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={page >= data.total_pages}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-white/5 disabled:opacity-30"
            >
              <ChevronRight size={15} />
            </button>
          </div>
        </AdminCard>
      )}
    </div>
  );
}
