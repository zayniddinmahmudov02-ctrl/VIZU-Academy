"use client";

import { isAxiosError } from "axios";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BarChart3, Calendar, Check, ChevronLeft, ChevronRight, CircleDollarSign, Clock3,
  Copy, Eye, Loader2, Pencil, Plus, Search, Sparkles, Ticket, Trash2, X,
} from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import AdminTabs from "@/components/admin/admin-tabs";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import BuyerCard from "@/features/admin/components/payments/buyer-card";
import HistoryDialog from "@/features/admin/components/payments/history-dialog";
import ReceiptViewer from "@/features/admin/components/payments/receipt-viewer";
import RejectDialog from "@/features/admin/components/payments/reject-dialog";
import { listPayments, type PaymentItem } from "@/features/admin/services/payment-service";
import {
  approveOrder,
  createPromoCode,
  deletePromoCode,
  extendOrderAccess,
  getPromoProducts,
  listBlockedUsers,
  listOrders,
  listPromoCodes,
  listPromoCodeOrders,
  rejectOrder,
  togglePromoCode,
  updatePromoCode,
} from "@/features/admin/services/vizu-pay-service";
import type {
  AdminOrderItem,
  BlockedUserItem,
  PromoCodeCreateRequest,
  PromoCodeItem,
  PromoCodeOrder,
} from "@/features/admin/types/vizu-pay.types";

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
  approved: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]",
  rejected: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
  refunded: "bg-white/5 text-[var(--admin-text-muted)]",
};

interface DateFilter {
  year?: number;
  month?: number;
  day?: number;
}

function DateFilterBar({ filter, onChange }: { filter: DateFilter; onChange: (f: DateFilter) => void }) {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 6 }, (_, i) => currentYear - i);

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <Calendar size={15} className="text-[var(--admin-text-muted)]" />
      <AdminSelect
        value={filter.year ?? ""}
        onChange={(e) => onChange({ ...filter, year: e.target.value ? Number(e.target.value) : undefined })}
        className="w-28"
      >
        <option value="">Jahr</option>
        {years.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </AdminSelect>
      <AdminSelect
        value={filter.month ?? ""}
        onChange={(e) => onChange({ ...filter, month: e.target.value ? Number(e.target.value) : undefined })}
        className="w-32"
        disabled={!filter.year}
      >
        <option value="">Monat</option>
        {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
          <option key={m} value={m}>
            {String(m).padStart(2, "0")}
          </option>
        ))}
      </AdminSelect>
      <AdminSelect
        value={filter.day ?? ""}
        onChange={(e) => onChange({ ...filter, day: e.target.value ? Number(e.target.value) : undefined })}
        className="w-28"
        disabled={!filter.month}
      >
        <option value="">Tag</option>
        {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
          <option key={d} value={d}>
            {String(d).padStart(2, "0")}
          </option>
        ))}
      </AdminSelect>
      {(filter.year || filter.month || filter.day) && (
        <AdminButton variant="ghost" size="sm" onClick={() => onChange({})}>
          Zurücksetzen
        </AdminButton>
      )}
    </div>
  );
}

const BUYER_SUB_TABS = [
  { value: "PENDING", label: "New Buyers" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
  { value: "BLOCKED", label: "Blocked" },
] as const;

type BuyerSubTab = (typeof BUYER_SUB_TABS)[number]["value"];

function actionErrorMessage(error: unknown, fallback: string): string {
  if (!isAxiosError<{ message?: string; detail?: string }>(error)) return fallback;
  return error.response?.data?.message ?? error.response?.data?.detail ?? fallback;
}

function BlockedUserCard({ user, onViewHistory }: { user: BlockedUserItem; onViewHistory: () => void }) {
  const name = [user.user_first_name, user.user_last_name].filter(Boolean).join(" ") || user.user_username;

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-[var(--admin-card)] p-4 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-danger)]/30">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-semibold text-[var(--admin-text-primary)]">{name}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{user.user_email}</p>
          {user.user_phone_number && (
            <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">{user.user_phone_number}</p>
          )}
        </div>
        <span className="shrink-0 rounded-full bg-[var(--admin-danger)]/15 px-2.5 py-1 text-xs font-semibold text-[var(--admin-danger)]">
          BLOCKED
        </span>
      </div>

      <p className="text-xs font-medium text-[var(--admin-danger)]">
        {user.rejection_count}/3 Ablehnungen
        {user.last_rejected_at && ` · Zuletzt: ${new Date(user.last_rejected_at).toLocaleDateString("de-DE")}`}
      </p>

      <button
        onClick={onViewHistory}
        className="w-fit rounded-lg ring-1 ring-[var(--admin-border-strong)] px-3 py-1.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-hover)]"
      >
        Verlauf ansehen
      </button>
    </div>
  );
}

function NewBuyersSection({ dateFilter }: { dateFilter: DateFilter }) {
  const queryClient = useQueryClient();
  const [subTab, setSubTab] = useState<BuyerSubTab>("PENDING");
  const [receiptOrder, setReceiptOrder] = useState<AdminOrderItem | null>(null);
  const [rejectingOrder, setRejectingOrder] = useState<AdminOrderItem | null>(null);
  const [historyTarget, setHistoryTarget] = useState<{ userId: string; userName: string } | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const ordersQuery = useQuery({
    queryKey: ["admin-orders", subTab, dateFilter],
    queryFn: () => listOrders({ status: subTab, page_size: 50, ...dateFilter }),
    enabled: subTab !== "BLOCKED",
  });

  const blockedQuery = useQuery({
    queryKey: ["admin-blocked-users"],
    queryFn: listBlockedUsers,
    enabled: subTab === "BLOCKED",
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
    queryClient.invalidateQueries({ queryKey: ["admin-blocked-users"] });
    queryClient.invalidateQueries({ queryKey: ["admin-orders-by-user"] });
  }

  const approveMutation = useMutation({
    mutationFn: approveOrder,
    onSuccess: invalidate,
    onError: (err: unknown) => setActionError(actionErrorMessage(err, "Genehmigung fehlgeschlagen.")),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => rejectOrder(id, reason),
    onSuccess: () => {
      invalidate();
      setRejectingOrder(null);
    },
    onError: (err: unknown) => setActionError(actionErrorMessage(err, "Ablehnung fehlgeschlagen.")),
  });

  const extendMutation = useMutation({
    mutationFn: ({ order, months, reason }: { order: AdminOrderItem; months: number; reason: string }) =>
      extendOrderAccess(order.id, months, reason),
    onSuccess: invalidate,
    onError: (err: unknown) => setActionError(actionErrorMessage(err, "Verlängerung fehlgeschlagen.")),
  });

  function buyerNameFor(order: AdminOrderItem) {
    return [order.user_first_name, order.user_last_name].filter(Boolean).join(" ") || order.user_username;
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {BUYER_SUB_TABS.map((t) => (
          <button
            key={t.value}
            onClick={() => setSubTab(t.value)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
              subTab === t.value
                ? "bg-[var(--admin-primary)] text-white"
                : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {actionError && (
        <div className="mb-4 rounded-xl bg-[var(--admin-danger)]/10 px-4 py-2.5 text-sm text-[var(--admin-danger)]">
          {actionError}
        </div>
      )}

      {subTab !== "BLOCKED" && (
        <>
          {ordersQuery.isLoading && (
            <div className="flex justify-center py-10">
              <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
            </div>
          )}

          {!ordersQuery.isLoading && (ordersQuery.data?.items.length ?? 0) === 0 && (
            <div className="rounded-2xl bg-[var(--admin-card)] px-6 py-16 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
              <p className="text-sm text-[var(--admin-text-muted)]">Keine Einträge in dieser Ansicht.</p>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {ordersQuery.data?.items.map((order) => (
              <BuyerCard
                key={order.id}
                order={order}
                onOpenReceipt={setReceiptOrder}
                onApprove={(o) => {
                  setActionError(null);
                  approveMutation.mutate(o.id);
                }}
                onReject={(o) => {
                  setActionError(null);
                  setRejectingOrder(o);
                }}
                onViewHistory={(o) => setHistoryTarget({ userId: o.user_id, userName: buyerNameFor(o) })}
                onExtend={(order, months, reason) => {
                  setActionError(null);
                  extendMutation.mutate({ order, months, reason });
                }}
                approvePending={approveMutation.isPending}
                extendPending={extendMutation.isPending}
              />
            ))}
          </div>
        </>
      )}

      {subTab === "BLOCKED" && (
        <>
          {blockedQuery.isLoading && (
            <div className="flex justify-center py-10">
              <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
            </div>
          )}

          {!blockedQuery.isLoading && (blockedQuery.data?.length ?? 0) === 0 && (
            <div className="rounded-2xl bg-[var(--admin-card)] px-6 py-16 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
              <p className="text-sm text-[var(--admin-text-muted)]">Keine blockierten Nutzer.</p>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {blockedQuery.data?.map((user) => (
              <BlockedUserCard
                key={user.user_id}
                user={user}
                onViewHistory={() =>
                  setHistoryTarget({
                    userId: user.user_id,
                    userName: [user.user_first_name, user.user_last_name].filter(Boolean).join(" ") || user.user_username,
                  })
                }
              />
            ))}
          </div>
        </>
      )}

      <ReceiptViewer order={receiptOrder} onClose={() => setReceiptOrder(null)} />

      <RejectDialog
        order={rejectingOrder}
        onClose={() => setRejectingOrder(null)}
        isPending={rejectMutation.isPending}
        onConfirm={(reason) => {
          if (!rejectingOrder) return;
          rejectMutation.mutate({ id: rejectingOrder.id, reason });
        }}
      />

      <HistoryDialog
        userId={historyTarget?.userId ?? null}
        userName={historyTarget?.userName ?? ""}
        onClose={() => setHistoryTarget(null)}
      />
    </div>
  );
}

// The legacy/generic Payment model (course-scoped, provider field) —
// reused as-is for the "Telegram" source view rather than building a
// second payment system. If it currently has 0 rows on this environment,
// that's an honest reflection of no Telegram-sourced payments existing
// here yet, not a bug.
function TelegramTab({ dateFilter }: { dateFilter: DateFilter }) {
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-telegram-payments", status, dateFilter],
    queryFn: () => listPayments({ status: status || undefined, page_size: 50, ...dateFilter }),
  });

  const columns: DataTableColumn<PaymentItem>[] = [
    {
      key: "user",
      header: "Nutzer",
      render: (item) => (
        <div>
          <p className="font-medium">{item.user_username ?? "—"}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{item.user_email ?? "—"}</p>
        </div>
      ),
    },
    {
      key: "date",
      header: "Datum",
      render: (item) => new Date(item.created_at).toLocaleDateString("de-DE"),
    },
    {
      key: "time",
      header: "Uhrzeit",
      render: (item) => new Date(item.created_at).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }),
    },
    { key: "amount", header: "Betrag", render: (item) => `${item.amount.toLocaleString()} ${item.currency}` },
    { key: "provider", header: "Quelle", render: (item) => item.provider },
    { key: "course", header: "Kurs", render: (item) => item.course_title ?? "—" },
    {
      key: "status",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            STATUS_STYLE[item.status] ?? "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.status}
        </span>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {["", "pending", "approved", "rejected"].map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
              status === s
                ? "bg-[var(--admin-primary)] text-white"
                : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]"
            }`}
          >
            {s || "Alle"}
          </button>
        ))}
      </div>

      <DataTable
        columns={columns}
        data={data?.items}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage="Keine Telegram-Zahlungen gefunden."
      />

      {data && data.total_pages > 1 && (
        <p className="mt-3 text-xs text-[var(--admin-text-muted)]">
          Seite {data.page} von {data.total_pages} ({data.total} Zahlungen)
        </p>
      )}
    </div>
  );
}

function PromoCodesTab() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error: loadError } = useQuery({ queryKey: ["promo-codes"], queryFn: listPromoCodes });
  const { data: products } = useQuery({ queryKey: ["promo-products"], queryFn: getPromoProducts });

  const [dialogOpen, setDialogOpen] = useState(false);
  type PromoForm = PromoCodeCreateRequest & {
    campaign: string;
    starts_at: string;
    expires_at: string;
    max_uses: number | null;
    is_active: boolean;
  };
  const EMPTY_FORM: PromoForm = {
    code: "",
    campaign: "",
    discount_type: "PERCENT",
    discount_value: 20,
    applicable_course_ids: [],
    applicable_package_codes: [],
    starts_at: "",
    max_uses: 100,
    max_uses_per_user: 1,
    expires_at: "",
    is_active: true,
  };
  const [form, setForm] = useState(EMPTY_FORM);
  const [editing, setEditing] = useState<PromoCodeItem | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  type PromoFormField = "code" | "discount_value" | "scope" | "max_uses" | "max_uses_per_user" | "dates";
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<PromoFormField, string>>>({});
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [productFilter, setProductFilter] = useState("ALL");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");
  const [page, setPage] = useState(1);
  const [details, setDetails] = useState<PromoCodeItem | null>(null);
  const [detailPage, setDetailPage] = useState(1);
  const [deleteTarget, setDeleteTarget] = useState<PromoCodeItem | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const orders = useQuery({
    queryKey: ["promo-orders", details?.id, detailPage],
    queryFn: () => listPromoCodeOrders(details!.id, detailPage),
    enabled: !!details,
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["promo-codes"] });
  }

  function toPayload(): PromoCodeCreateRequest {
    return {
      ...form,
      campaign: form.campaign.trim() || null,
      starts_at: form.starts_at ? new Date(form.starts_at).toISOString() : null,
      max_uses: form.max_uses || null,
      expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
      is_active: form.is_active,
    };
  }

  const saveMutation = useMutation({
    mutationFn: () => editing
      ? updatePromoCode(editing.id, toPayload())
      : createPromoCode(toPayload()),
    onSuccess: () => {
      invalidate();
      setDialogOpen(false);
      setForm(EMPTY_FORM);
      setEditing(null);
      setSaveError(null);
      setFieldErrors({});
    },
    onError: (error) => setSaveError(actionErrorMessage(error, "Promo-Code konnte nicht gespeichert werden.")),
  });
  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) => togglePromoCode(id, isActive),
    onSuccess: invalidate,
  });
  const deleteMutation = useMutation({
    mutationFn: deletePromoCode,
    onSuccess: () => { invalidate(); setDeleteTarget(null); },
  });

  function beginCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setSaveError(null);
    setFieldErrors({});
    setDialogOpen(true);
  }

  function beginEdit(item: PromoCodeItem) {
    const localDateTime = (value: string | null) => {
      if (!value) return "";
      const date = new Date(value);
      return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
    };
    setEditing(item);
    setForm({
      code: item.code,
      campaign: item.campaign ?? "",
      discount_type: item.discount_type,
      discount_value: item.discount_value,
      applicable_course_ids: item.applicable_course_ids,
      applicable_package_codes: item.applicable_package_codes,
      starts_at: localDateTime(item.starts_at),
      max_uses: item.max_uses,
      max_uses_per_user: item.max_uses_per_user,
      expires_at: localDateTime(item.expires_at),
      is_active: item.is_active,
    });
    setSaveError(null);
    setFieldErrors({});
    setDialogOpen(true);
  }

  function toggleProduct(key: "applicable_course_ids" | "applicable_package_codes", value: string) {
    const current = form[key];
    setForm({ ...form, [key]: current.includes(value) ? current.filter((entry) => entry !== value) : [...current, value] });
  }

  const money = (value: number) => `${new Intl.NumberFormat("de-DE").format(value)} UZS`;
  const counts = useMemo(() => {
    const items = data ?? [];
    return {
      active: items.filter((item) => item.status === "ACTIVE").length,
      scheduled: items.filter((item) => item.status === "SCHEDULED").length,
      expired: items.filter((item) => item.status === "EXPIRED").length,
      inactive: items.filter((item) => ["INACTIVE", "EXHAUSTED"].includes(item.status)).length,
      uses: items.reduce((total, item) => total + item.successful_uses, 0),
      discount: items.reduce((total, item) => total + item.successful_discount_amount, 0),
      revenue: items.reduce((total, item) => total + item.successful_revenue_amount, 0),
    };
  }, [data]);
  const filtered = useMemo(() => (data ?? []).filter((item) => {
    const q = search.trim().toLowerCase();
    const matchesSearch = !q || `${item.code} ${item.campaign ?? ""}`.toLowerCase().includes(q);
    const matchesStatus = statusFilter === "ALL" || item.status === statusFilter;
    const matchesType = typeFilter === "ALL" || item.discount_type === typeFilter;
    const matchesProduct = productFilter === "ALL"
      || item.applicable_course_ids.includes(productFilter)
      || item.applicable_package_codes.includes(productFilter);
    const created = new Date(item.created_at).getTime();
    const matchesFrom = !createdFrom || created >= new Date(`${createdFrom}T00:00:00`).getTime();
    const matchesTo = !createdTo || created <= new Date(`${createdTo}T23:59:59.999`).getTime();
    return matchesSearch && matchesStatus && matchesType && matchesProduct && matchesFrom && matchesTo;
  }), [data, search, statusFilter, typeFilter, productFilter, createdFrom, createdTo]);
  const pageSize = 10;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const visiblePromos = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const hasProducts = form.discount_type !== "FREE_DAYS";
  const selectedTargets = form.applicable_course_ids.length + form.applicable_package_codes.length;

  function validateForm(): Partial<Record<PromoFormField, string>> {
    const errors: Partial<Record<PromoFormField, string>> = {};
    const code = form.code.trim();
    if (!/^[a-z0-9_-]{1,40}$/i.test(code)) errors.code = "Kod harf, raqam, tire yoki pastki chiziqdan iborat bo‘lsin (maks. 40 belgi).";
    if (!Number.isInteger(form.discount_value) || form.discount_value <= 0) errors.discount_value = "Qiymat 0 dan katta butun son bo‘lishi kerak.";
    else if (form.discount_type === "PERCENT" && form.discount_value > 100) errors.discount_value = "Foiz 100 dan oshmasligi kerak.";
    if (hasProducts && selectedTargets === 0) errors.scope = "Kamida bitta kurs yoki paketni aniq tanlang.";
    if (form.max_uses !== null && (!Number.isInteger(form.max_uses) || form.max_uses < 1)) errors.max_uses = "Kamida 1 bo‘lsin yoki maydonni bo‘sh qoldiring.";
    if (!Number.isInteger(form.max_uses_per_user) || form.max_uses_per_user < 1) errors.max_uses_per_user = "Foydalanuvchi limiti kamida 1 bo‘lishi kerak.";
    if (form.starts_at && form.expires_at && form.starts_at >= form.expires_at) errors.dates = "Tugash vaqti boshlanish vaqtidan keyin bo‘lishi kerak.";
    return errors;
  }

  function submitForm() {
    const validation = validateForm();
    setFieldErrors(validation);
    if (Object.keys(validation).length) {
      setSaveError("Maydonlardagi xatolarni tuzating.");
      return;
    }
    setSaveError(null);
    saveMutation.mutate();
  }

  function generateCode() {
    const token = Math.random().toString(36).slice(2, 8).toUpperCase();
    setFieldErrors((current) => ({ ...current, code: undefined }));
    setForm((current) => ({ ...current, code: `VIZU${token}` }));
  }

  async function copyCode(item: PromoCodeItem) {
    try {
      await navigator.clipboard.writeText(item.code);
      setCopiedId(item.id);
      window.setTimeout(() => setCopiedId((current) => current === item.id ? null : current), 1500);
    } catch {
      setSaveError("Kod nusxalanmadi. Brauzer clipboard ruxsatini tekshiring.");
    }
  }

  const columns: DataTableColumn<PromoCodeItem>[] = [
    {
      key: "code",
      header: "Promokod",
      render: (item) => (
        <div className="min-w-32">
          <div className="flex items-center gap-1.5">
            <span className="font-mono font-bold tracking-wide">{item.code}</span>
            <button type="button" aria-label={`${item.code} nusxalash`} onClick={() => void copyCode(item)} className="rounded p-1 text-[var(--admin-text-muted)] hover:text-[var(--admin-primary)]">
              {copiedId === item.id ? <Check size={13} /> : <Copy size={13} />}
            </button>
          </div>
          <span className="text-xs text-[var(--admin-text-muted)]">{item.campaign || "Ichki izoh yo‘q"}</span>
        </div>
      ),
    },
    {
      key: "type",
      header: "Chegirma",
      render: (item) => (
        <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
          {item.discount_type === "PERCENT" ? <>{item.discount_value}% · Foiz</>
            : item.discount_type === "SPECIAL_PRICE" ? <>Maxsus narx · {money(item.discount_value)}</>
              : item.discount_type === "FIXED" ? <>{money(item.discount_value)} chegirma</>
                : <>Premium · {item.discount_value} kun</>}
        </span>
      ),
    },
    {
      key: "products",
      header: "Kurs / paket",
      render: (item) => {
        const selectedCourses = (products?.courses ?? []).filter((course) => item.applicable_course_ids.includes(course.id));
        const selectedPackages = (products?.packages ?? []).filter((pkg) => item.applicable_package_codes.includes(pkg.code));
        const labels = [...selectedCourses.map((course) => course.level), ...selectedPackages.map((pkg) => pkg.label)];
        return <span className="block max-w-48 truncate text-xs" title={labels.join(", ") || "Premium"}>{labels.join(", ") || "Premium"}</span>;
      },
    },
    {
      key: "validity",
      header: "Boshlanish / tugash",
      render: (item) => (
        <div className="whitespace-nowrap text-xs text-[var(--admin-text-secondary)]">
          <div>{item.starts_at ? new Date(item.starts_at).toLocaleString("uz-UZ") : "Darhol"}</div>
          <div>{item.expires_at ? new Date(item.expires_at).toLocaleString("uz-UZ") : "Cheklanmagan"}</div>
        </div>
      ),
    },
    {
      key: "usage",
      header: "Foydalanish",
      render: (item) => (
        <div className="min-w-28">
          <div>{item.used_count} / {item.max_uses ?? "∞"}</div>
          <div className="text-xs text-[var(--admin-text-muted)]">{item.successful_uses} paid · {item.remaining_uses ?? "∞"} qoldi</div>
        </div>
      ),
    },
    {
      key: "status",
      header: "Holat",
      render: (item) => {
        const label: Record<string, string> = { ACTIVE: "Faol", SCHEDULED: "Rejalashtirilgan", EXPIRED: "Muddati tugagan", EXHAUSTED: "Limit tugagan", INACTIVE: "Nofaol" };
        const style = item.status === "ACTIVE" ? "text-[var(--admin-success)] bg-[var(--admin-success)]/10"
          : item.status === "SCHEDULED" ? "text-[var(--admin-primary)] bg-[var(--admin-primary)]/10"
            : "text-[var(--admin-text-muted)] bg-white/5";
        return <span className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${style}`}>{label[item.status] ?? item.status}</span>;
      },
    },
    {
      key: "created",
      header: "Yaratilgan",
      render: (item) => <span className="whitespace-nowrap text-xs text-[var(--admin-text-secondary)]">{new Date(item.created_at).toLocaleDateString("uz-UZ")}</span>,
    },
    {
      key: "actions",
      header: "Amallar",
      render: (item) => (
        <div className="flex items-center gap-1">
          <button type="button" title="Tafsilotlar va statistika" aria-label={`${item.code} tafsilotlari`} onClick={() => setDetails(item)} className="rounded-lg p-2 text-[var(--admin-text-secondary)] hover:bg-white/5"><Eye size={15} /></button>
          <button type="button" title="Tahrirlash" aria-label={`${item.code} tahrirlash`} onClick={() => beginEdit(item)} className="rounded-lg p-2 text-[var(--admin-text-secondary)] hover:bg-white/5"><Pencil size={15} /></button>
          <button type="button" title={item.is_active ? "Deaktivatsiya" : "Faollashtirish"} aria-label={item.is_active ? `${item.code} deaktivatsiya` : `${item.code} faollashtirish`} disabled={toggleMutation.isPending} onClick={() => toggleMutation.mutate({ id: item.id, isActive: !item.is_active })} className="rounded-lg p-2 text-[var(--admin-text-secondary)] hover:bg-white/5">{item.is_active ? <X size={15} /> : <Check size={15} />}</button>
          <button type="button" title="O‘chirish" aria-label={`${item.code} o‘chirish`} disabled={item.used_count > 0} onClick={() => setDeleteTarget(item)} className="rounded-lg p-2 text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)] disabled:opacity-30"><Trash2 size={15} /></button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-5" data-testid="promo-codes-tab">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold text-[var(--admin-text-primary)]">Promo Codes</h2>
          <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">Promokodlar, chegirmalar va foydalanish statistikasini boshqaring.</p>
        </div>
        <AdminButton onClick={beginCreate}>
          <Plus size={16} />
          Yangi promokod
        </AdminButton>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-7">
        {[
          { label: "Faol", value: counts.active, icon: Check },
          { label: "Rejalashtirilgan", value: counts.scheduled, icon: Clock3 },
          { label: "Muddati tugagan", value: counts.expired, icon: Calendar },
          { label: "Nofaol", value: counts.inactive, icon: X },
          { label: "Muvaffaqiyatli foydalanish", value: counts.uses, icon: Ticket },
          { label: "Chegirma jami", value: money(counts.discount), icon: CircleDollarSign },
          { label: "Promo tushumi", value: money(counts.revenue), icon: BarChart3 },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="min-w-0 rounded-2xl bg-[var(--admin-card)] p-3.5 ring-1 ring-[var(--admin-border)] sm:p-4">
            <div className="flex items-center gap-2 text-xs text-[var(--admin-text-muted)]"><Icon size={14} />{label}</div>
            <div className="mt-2 truncate text-lg font-bold text-[var(--admin-text-primary)]" title={String(value)}>{isLoading ? "—" : value}</div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl bg-[var(--admin-card)] p-3.5 ring-1 ring-[var(--admin-border)] sm:p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-6">
          <label className="relative sm:col-span-2 xl:col-span-2">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
            <AdminInput className="pl-9" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Kod yoki izoh bo‘yicha qidirish" aria-label="Promokod qidirish" />
          </label>
          <AdminSelect aria-label="Promokod holati" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1); }}>
            <option value="ALL">Barcha holatlar</option><option value="ACTIVE">Faol</option><option value="SCHEDULED">Rejalashtirilgan</option><option value="EXPIRED">Muddati tugagan</option><option value="INACTIVE">Nofaol</option><option value="EXHAUSTED">Limit tugagan</option>
          </AdminSelect>
          <AdminSelect aria-label="Chegirma turi" value={typeFilter} onChange={(event) => { setTypeFilter(event.target.value); setPage(1); }}>
            <option value="ALL">Barcha chegirmalar</option><option value="PERCENT">Foizli chegirma</option><option value="SPECIAL_PRICE">Maxsus narx</option><option value="FIXED">Belgilangan summa</option><option value="FREE_DAYS">Premium kunlari</option>
          </AdminSelect>
          <AdminSelect aria-label="Kurs yoki paket" value={productFilter} onChange={(event) => { setProductFilter(event.target.value); setPage(1); }}>
            <option value="ALL">Barcha mahsulotlar</option>
            {(products?.courses ?? []).map((course) => <option key={course.id} value={course.id}>{course.level} · {course.title}</option>)}
            {(products?.packages ?? []).map((product) => <option key={product.code} value={product.code}>{product.label}</option>)}
          </AdminSelect>
          <div className="flex gap-2">
            <AdminInput type="date" aria-label="Yaratilgan sanadan" value={createdFrom} onChange={(event) => { setCreatedFrom(event.target.value); setPage(1); }} />
            <AdminInput type="date" aria-label="Yaratilgan sanagacha" value={createdTo} onChange={(event) => { setCreatedTo(event.target.value); setPage(1); }} />
          </div>
        </div>
      </div>

      {isError && <div className="rounded-xl bg-[var(--admin-danger)]/10 p-4 text-sm text-[var(--admin-danger)]" role="alert">{actionErrorMessage(loadError, "Promokodlar yuklanmadi.")}</div>}
      {toggleMutation.isError && <div className="rounded-xl bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]" role="alert">{actionErrorMessage(toggleMutation.error, "Holatni yangilash amalga oshmadi.")}</div>}

      <DataTable
        columns={columns}
        data={visiblePromos}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage={data?.length ? "Tanlangan filtrlar bo‘yicha promokod topilmadi." : "Hozircha promokod yo‘q. Birinchi kodni yarating."}
      />

      <div className="flex flex-col gap-2 text-sm text-[var(--admin-text-secondary)] sm:flex-row sm:items-center sm:justify-between">
        <span>{filtered.length} ta natija · jami {data?.length ?? 0} ta promokod</span>
        <div className="flex items-center gap-2">
          <AdminButton variant="secondary" size="sm" disabled={currentPage <= 1} onClick={() => setPage(currentPage - 1)} aria-label="Oldingi sahifa"><ChevronLeft size={15} />Oldingi</AdminButton>
          <span>{currentPage} / {pageCount}</span>
          <AdminButton variant="secondary" size="sm" disabled={currentPage >= pageCount} onClick={() => setPage(currentPage + 1)} aria-label="Keyingi sahifa">Keyingi<ChevronRight size={15} /></AdminButton>
        </div>
      </div>

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Promokodni tahrirlash" : "Yangi promokod"}
        description="Kod narxi, mahsulot qamrovi va foydalanish cheklovlari serverda qayta tekshiriladi."
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Bekor qilish
            </AdminButton>
            <AdminButton
              onClick={submitForm}
              disabled={saveMutation.isPending}
            >
              {saveMutation.isPending ? <><Loader2 size={15} className="animate-spin" />Saqlanmoqda…</> : editing ? "Saqlash" : "Promokod yaratish"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-5">
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Asosiy ma’lumotlar</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <AdminLabel htmlFor="promo-code">Promokod</AdminLabel>
                <div className="flex gap-2">
                  <AdminInput id="promo-code" autoComplete="off" maxLength={40} value={form.code} aria-invalid={!!fieldErrors.code} onChange={(e) => { setSaveError(null); setFieldErrors((current) => ({ ...current, code: undefined })); setForm({ ...form, code: e.target.value.toUpperCase().replace(/[^A-Z0-9_-]/g, "") }); }} placeholder="VIZU70" />
                  {!editing && <AdminButton type="button" variant="secondary" onClick={generateCode} aria-label="Promokod generatsiya qilish"><Sparkles size={15} />Generatsiya</AdminButton>}
                </div>
                {fieldErrors.code && <p className="mt-1 text-xs text-[var(--admin-danger)]" role="alert">{fieldErrors.code}</p>}
              </div>
              <div>
                <AdminLabel htmlFor="promo-campaign">Tavsif / ichki izoh</AdminLabel>
                <AdminInput id="promo-campaign" maxLength={120} value={form.campaign} onChange={(e) => setForm({ ...form, campaign: e.target.value })} placeholder="Mavsumiy kampaniya" />
              </div>
            </div>
            <label className="inline-flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
              <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
              Saqlanganda promokod faol bo‘lsin
            </label>
          </section>
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Chegirma shartlari</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel htmlFor="promo-type">Chegirma turi</AdminLabel>
              <AdminSelect
                id="promo-type"
                value={form.discount_type}
                onChange={(e) => setForm({ ...form, discount_type: e.target.value, applicable_course_ids: e.target.value === "FREE_DAYS" ? [] : form.applicable_course_ids, applicable_package_codes: e.target.value === "FREE_DAYS" ? [] : form.applicable_package_codes })}
              >
                <option value="PERCENT">Foizli chegirma</option>
                <option value="SPECIAL_PRICE">Yakuniy maxsus narx</option>
                <option value="FIXED">Belgilangan summa chegirmasi</option>
                <option value="FREE_DAYS">Premium kunlari</option>
              </AdminSelect>
            </div>
            <div>
              <AdminLabel htmlFor="promo-value">{form.discount_type === "PERCENT" ? "Chegirma foizi" : form.discount_type === "FREE_DAYS" ? "Premium kunlari" : form.discount_type === "SPECIAL_PRICE" ? "Yakuniy narx (UZS)" : "Chegirma summasi (UZS)"}</AdminLabel>
              <AdminInput
                id="promo-value"
                type="number"
                min={form.discount_type === "SPECIAL_PRICE" ? 0 : 1}
                max={form.discount_type === "PERCENT" ? 100 : undefined}
                value={form.discount_value}
                aria-invalid={!!fieldErrors.discount_value}
                onChange={(e) => { setFieldErrors((current) => ({ ...current, discount_value: undefined })); setForm({ ...form, discount_value: Number(e.target.value) }); }}
              />
              {fieldErrors.discount_value && <p className="mt-1 text-xs text-[var(--admin-danger)]" role="alert">{fieldErrors.discount_value}</p>}
            </div>
          </div>
          </section>

          {form.discount_type === "FREE_DAYS" && (
            <div className="flex gap-2">
              {[1, 3, 7, 30].map((days) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => setForm({ ...form, discount_value: days })}
                  className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                    form.discount_value === days
                      ? "bg-[var(--admin-primary)] text-white"
                      : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]"
                  }`}
                >
                  {days} kun
                </button>
              ))}
            </div>
          )}

          {hasProducts && (
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <AdminLabel className="mb-0">Mahsulotlar · {selectedTargets} tanlangan</AdminLabel>
                  <button
                    type="button"
                    className="text-xs font-semibold text-[var(--admin-primary)] hover:underline"
                                onClick={() => {
                                  setFieldErrors((current) => ({ ...current, scope: undefined }));
                                  setForm({
                                    ...form,
                                    applicable_course_ids: (products?.courses ?? []).map((course) => course.id),
                                    applicable_package_codes: (products?.packages ?? []).map((product) => product.code),
                                  });
                                }}
                  >Barchasini tanlash</button>
                </div>
                <p className="text-xs text-[var(--admin-text-muted)]">Faqat belgilangan kurs va paketlarga qo‘llanadi. Bo‘sh scope barcha mahsulotlarni anglatmaydi.</p>
                <div className="mt-1 max-h-36 space-y-1 overflow-y-auto rounded-lg border border-[var(--admin-border)] p-2">
                  {(products?.courses ?? []).map((course) => (
                    <label key={course.id} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={form.applicable_course_ids.includes(course.id)}
                        onChange={() => { setFieldErrors((current) => ({ ...current, scope: undefined })); toggleProduct("applicable_course_ids", course.id); }}
                      />
                      <span>{course.title} ({course.level})</span>
                    </label>
                  ))}
                  {products?.courses.length === 0 && <p className="text-xs text-[var(--admin-text-muted)]">Mos faol kurs topilmadi.</p>}
                </div>
              </div>
              <div>
                <AdminLabel>Paketlar</AdminLabel>
                <div className="mt-1 flex flex-wrap gap-3">
                  {(products?.packages ?? []).map((product) => (
                    <label key={product.code} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={form.applicable_package_codes.includes(product.code)}
                        onChange={() => { setFieldErrors((current) => ({ ...current, scope: undefined })); toggleProduct("applicable_package_codes", product.code); }}
                      />
                      <span>{product.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              {fieldErrors.scope && <p className="text-xs text-[var(--admin-danger)]" role="alert">{fieldErrors.scope}</p>}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel>Umumiy foydalanish limiti (bo‘sh = cheksiz)</AdminLabel>
              <AdminInput
                type="number"
                value={form.max_uses ?? ""}
                aria-invalid={!!fieldErrors.max_uses}
                onChange={(e) => { setFieldErrors((current) => ({ ...current, max_uses: undefined })); setForm({ ...form, max_uses: e.target.value ? Number(e.target.value) : null }); }}
                placeholder="100"
              />
              {fieldErrors.max_uses && <p className="mt-1 text-xs text-[var(--admin-danger)]" role="alert">{fieldErrors.max_uses}</p>}
            </div>
            <div>
              <AdminLabel>Bitta foydalanuvchi uchun limit</AdminLabel>
              <AdminInput
                type="number"
                min={1}
                value={form.max_uses_per_user}
                aria-invalid={!!fieldErrors.max_uses_per_user}
                onChange={(e) => { setFieldErrors((current) => ({ ...current, max_uses_per_user: undefined })); setForm({ ...form, max_uses_per_user: Number(e.target.value) }); }}
              />
              {fieldErrors.max_uses_per_user && <p className="mt-1 text-xs text-[var(--admin-danger)]" role="alert">{fieldErrors.max_uses_per_user}</p>}
            </div>
            <div>
              <AdminLabel>Boshlanish sanasi va vaqti</AdminLabel>
              <AdminInput
                type="datetime-local"
                value={form.starts_at}
                aria-invalid={!!fieldErrors.dates}
                onChange={(e) => { setFieldErrors((current) => ({ ...current, dates: undefined })); setForm({ ...form, starts_at: e.target.value }); }}
              />
            </div>
            <div>
              <AdminLabel>Tugash sanasi va vaqti</AdminLabel>
              <AdminInput
                type="datetime-local"
                value={form.expires_at}
                aria-invalid={!!fieldErrors.dates}
                onChange={(e) => { setFieldErrors((current) => ({ ...current, dates: undefined })); setForm({ ...form, expires_at: e.target.value }); }}
              />
            </div>
            {fieldErrors.dates && <p className="col-span-2 text-xs text-[var(--admin-danger)]" role="alert">{fieldErrors.dates}</p>}
          </div>
          {saveError && <p className="rounded-lg bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]" role="alert">{saveError}</p>}
        </div>
      </FormDialog>

      <FormDialog
        open={!!details}
        onOpenChange={(open) => {
          if (!open) {
            setDetails(null);
            setDetailPage(1);
          }
        }}
        title={details ? `Promokod: ${details.code}` : "Promokod tafsilotlari"}
        description="To‘lovlar va narx snapshotlari buyurtma yaratilgan vaqtdagi qiymatlarni ko‘rsatadi."
        size="lg"
      >
        {details && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ["Muvaffaqiyatli xarid", details.successful_uses],
                ["Ishlatilgan limit", `${details.used_count} / ${details.max_uses ?? "∞"}`],
                ["Chegirmalar", money(details.successful_discount_amount)],
                ["Tushum", money(details.successful_revenue_amount)],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl bg-[var(--admin-card)] p-3 ring-1 ring-[var(--admin-border)]">
                  <div className="text-xs text-[var(--admin-text-muted)]">{label}</div>
                  <div className="mt-1 text-sm font-bold text-[var(--admin-text-primary)]">{value}</div>
                </div>
              ))}
            </div>
            {orders.isError && <p className="text-sm text-[var(--admin-danger)]" role="alert">{actionErrorMessage(orders.error, "Buyurtmalar tarixi yuklanmadi.")}</p>}
            {orders.isLoading ? (
              <div className="flex items-center justify-center gap-2 py-8 text-sm text-[var(--admin-text-muted)]"><Loader2 size={16} className="animate-spin" />Buyurtmalar yuklanmoqda…</div>
            ) : orders.data?.items.length ? (
              <>
                <div className="space-y-2">
                  {orders.data.items.map((order: PromoCodeOrder) => (
                    <article key={order.id} className="grid gap-2 rounded-xl border border-[var(--admin-border)] p-3 text-sm sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                      <div className="min-w-0">
                        <div className="font-semibold text-[var(--admin-text-primary)]">{order.product_name} <span className="text-xs font-normal text-[var(--admin-text-muted)]">· {order.product_code}</span></div>
                        <div className="truncate text-xs text-[var(--admin-text-secondary)]">{order.user_name} · {order.user_email}</div>
                        <div className="text-xs text-[var(--admin-text-muted)]">{new Date(order.created_at).toLocaleString("uz-UZ")}{order.reviewed_at ? ` · ko‘rib chiqilgan ${new Date(order.reviewed_at).toLocaleString("uz-UZ")}` : ""}</div>
                      </div>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 sm:justify-end">
                        <span className="text-xs text-[var(--admin-text-muted)]">{order.status}</span>
                        <span className="text-xs text-[var(--admin-text-secondary)]">{money(order.base_amount)} − {money(order.discount_amount)}</span>
                        <strong className="text-sm text-[var(--admin-text-primary)]">{money(order.final_amount)}</strong>
                      </div>
                    </article>
                  ))}
                </div>
                {orders.data.total_pages > 1 && (
                  <div className="flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
                    <span>{orders.data.total} ta buyurtma · {orders.data.page} / {orders.data.total_pages}</span>
                    <div className="flex gap-2">
                      <AdminButton variant="secondary" size="sm" disabled={detailPage <= 1} onClick={() => setDetailPage((value) => value - 1)}><ChevronLeft size={14} />Oldingi</AdminButton>
                      <AdminButton variant="secondary" size="sm" disabled={detailPage >= orders.data.total_pages} onClick={() => setDetailPage((value) => value + 1)}>Keyingi<ChevronRight size={14} /></AdminButton>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="rounded-xl border border-dashed border-[var(--admin-border)] p-6 text-center text-sm text-[var(--admin-text-muted)]">Bu promokod bilan buyurtmalar topilmadi.</div>
            )}
          </div>
        )}
      </FormDialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Promokodni o‘chirish"
        description={deleteTarget ? `${deleteTarget.code} promokodi o‘chiriladi. Bu amalni ortga qaytarib bo‘lmaydi.` : ""}
        confirmLabel="O‘chirish"
        pendingLabel="O‘chirilmoqda…"
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        isPending={deleteMutation.isPending}
        error={deleteMutation.isError ? actionErrorMessage(deleteMutation.error, "Promokod o‘chirilmadi.") : null}
      />
    </div>
  );
}

export default function PaymentsPage() {
  const [dateFilter, setDateFilter] = useState<DateFilter>({});

  return (
    <div>
      <AdminPageHeader title="Payments" description="Zahlungen prüfen, genehmigen und Promo-Codes verwalten." />
      <DateFilterBar filter={dateFilter} onChange={setDateFilter} />
      <AdminTabs
        defaultValue="new-buyers"
        tabs={[
          { value: "new-buyers", label: "New Buyers", content: <NewBuyersSection dateFilter={dateFilter} /> },
          { value: "telegram", label: "Telegram", content: <TelegramTab dateFilter={dateFilter} /> },
          { value: "promos", label: "Promo-Codes", content: <PromoCodesTab /> },
        ]}
      />
    </div>
  );
}
