"use client";

import { isAxiosError } from "axios";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Ban, BarChart3, Calendar, Check, ChevronLeft, ChevronRight, CircleDollarSign, Clock3,
  Copy, Eye, Hourglass, Loader2, Pencil, Plus, Search, ShieldCheck, Sparkles, Ticket, Trash2, X,
} from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import AdminTabs from "@/components/admin/admin-tabs";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import BuyerCard from "@/features/admin/components/payments/buyer-card";
import HistoryDialog from "@/features/admin/components/payments/history-dialog";
import { OrdersHistoryTab, PromoRequestsTab } from "@/features/admin/components/payments/payment-tabs";
import { MlEntitlementsList, PaymentSettingsTab, PaymentsOverviewTab } from "@/features/admin/components/payments/payments-sections";
import ReceiptViewer from "@/features/admin/components/payments/receipt-viewer";
import RejectDialog from "@/features/admin/components/payments/reject-dialog";
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
  reviewPromoCode,
  setOrderNote,
  updatePromoCode,
} from "@/features/admin/services/vizu-pay-service";
import type {
  AdminOrderItem,
  BlockedUserItem,
  ProductCategory,
  PromoCodeCreateRequest,
  PromoCodeItem,
  PromoCodeOrder,
  PromoReviewAction,
} from "@/features/admin/types/vizu-pay.types";

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

/** Payment requests as cards (approve / reject / note / receipt). `kind`: all products, course orders only, or the Multilevel Premium. */
function NewBuyersSection({ dateFilter, kind }: { dateFilter: DateFilter; kind?: "course" | "multilevel" }) {
  const queryClient = useQueryClient();
  const [subTab, setSubTab] = useState<BuyerSubTab>("PENDING");
  const [receiptOrder, setReceiptOrder] = useState<AdminOrderItem | null>(null);
  const [rejectingOrder, setRejectingOrder] = useState<AdminOrderItem | null>(null);
  const [historyTarget, setHistoryTarget] = useState<{ userId: string; userName: string } | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const ordersQuery = useQuery({
    queryKey: ["admin-orders", kind ?? "all", subTab, dateFilter],
    queryFn: () => listOrders({ status: subTab, page_size: 50, kind, ...dateFilter }),
    enabled: subTab !== "BLOCKED",
  });

  const noteMutation = useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) => setOrderNote(id, note),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-orders"] }),
    onError: (err: unknown) => setActionError(actionErrorMessage(err, "Notiz konnte nicht gespeichert werden.")),
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
    queryClient.invalidateQueries({ queryKey: ["admin-payments-overview"] });
    queryClient.invalidateQueries({ queryKey: ["admin-ml-entitlements"] });
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
                onNote={(o, note) => {
                  setActionError(null);
                  noteMutation.mutate({ id: o.id, note });
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
    requires_approval: boolean;
    product_category: ProductCategory;
  };
  const EMPTY_FORM: PromoForm = {
    product_category: "COURSES",
    requires_approval: false,
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
    is_active: false,
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
  const [detailSearch, setDetailSearch] = useState("");
  const [detailPlan, setDetailPlan] = useState("");
  const orders = useQuery({
    queryKey: ["promo-orders", details?.id, detailPage, detailSearch, detailPlan],
    queryFn: () => listPromoCodeOrders(details!.id, detailPage, 20, { search: detailSearch, plan: detailPlan }),
    enabled: !!details,
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["promo-codes"] });
  }

  function toPayload(): PromoCodeCreateRequest {
    const multilevel = form.product_category === "MULTILEVEL";
    const payload: PromoCodeCreateRequest = {
      ...form,
      campaign: form.campaign.trim() || null,
      starts_at: form.starts_at ? new Date(form.starts_at).toISOString() : null,
      max_uses: form.max_uses || null,
      expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
      // a category names only its own products (the server checks it again)
      applicable_course_ids: form.product_category === "COURSES" ? form.applicable_course_ids : [],
      applicable_package_codes: form.product_category === "PACKAGES" ? form.applicable_package_codes : [],
      requires_approval: !multilevel && ["PERCENT", "FIXED", "SPECIAL_PRICE"].includes(form.discount_type) && form.requires_approval,
    };
    // on/off is the approval workflow (review buttons), never part of a save; a new code always starts PENDING
    delete payload.is_active;
    return payload;
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
    mutationFn: ({ id, action, note }: { id: string; action: PromoReviewAction; note?: string }) => reviewPromoCode(id, action, note),
    onSuccess: () => { invalidate(); queryClient.invalidateQueries({ queryKey: ["admin-payments-overview"] }); },
  });

  function review(item: PromoCodeItem, action: PromoReviewAction) {
    let note: string | undefined;
    if (action === "reject") {
      const answer = window.prompt(`${item.code}: rad etish sababi (ixtiyoriy)`);
      if (answer === null) return;
      note = answer;
    }
    toggleMutation.mutate({ id: item.id, action, note });
  }
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
      requires_approval: !!item.requires_approval,
      product_category: item.product_category ?? "COURSES",
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
      pending: items.filter((item) => item.status === "PENDING").length,
      scheduled: items.filter((item) => item.status === "SCHEDULED").length,
      expired: items.filter((item) => item.status === "EXPIRED").length,
      inactive: items.filter((item) => ["INACTIVE", "EXHAUSTED", "DISABLED", "REJECTED", "APPROVED"].includes(item.status)).length,
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
      || (productFilter === "MULTILEVEL" && item.product_category === "MULTILEVEL")
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
  const isMultilevel = form.product_category === "MULTILEVEL";
  const hasProducts = form.discount_type !== "FREE_DAYS" && !isMultilevel;
  const isFreeAccess = form.discount_type === "FREE_ACCESS";
  const selectedTargets = form.product_category === "COURSES" ? form.applicable_course_ids.length : form.applicable_package_codes.length;
  // discount types per category (the server has the same list: admin_service.CATEGORY_DISCOUNT_TYPES)
  const TYPES_BY_CATEGORY: Record<ProductCategory, string[]> = {
    COURSES: ["PERCENT", "SPECIAL_PRICE", "FIXED", "FREE_DAYS", "FREE_ACCESS"],
    PACKAGES: ["PERCENT", "SPECIAL_PRICE", "FIXED", "FREE_ACCESS"],
    MULTILEVEL: ["PERCENT", "FREE_ACCESS"],
  };
  const TYPE_LABEL: Record<string, string> = {
    PERCENT: "Foizli chegirma", SPECIAL_PRICE: "Yakuniy maxsus narx", FIXED: "Belgilangan summa chegirmasi", FREE_DAYS: "Premium kunlari",
    FREE_ACCESS: "Bepul taqdim etish (100%)",
  };
  const CATEGORY_LABEL: Record<ProductCategory, string> = { COURSES: "Kurslar", PACKAGES: "Paketlar", MULTILEVEL: "Multilevel Modelltest" };

  function validateForm(): Partial<Record<PromoFormField, string>> {
    const errors: Partial<Record<PromoFormField, string>> = {};
    const code = form.code.trim();
    if (!/^[a-z0-9_-]{1,40}$/i.test(code)) errors.code = "Kod harf, raqam, tire yoki pastki chiziqdan iborat bo‘lsin (maks. 40 belgi).";
    if (isFreeAccess) { /* no value: the server stores a full waiver */ }
    else if (!Number.isInteger(form.discount_value) || form.discount_value <= 0) errors.discount_value = "Qiymat 0 dan katta butun son bo‘lishi kerak.";
    else if (form.discount_type === "PERCENT" && form.discount_value > 100) errors.discount_value = "Foiz 100 dan oshmasligi kerak.";
    if (hasProducts && selectedTargets === 0) errors.scope = form.product_category === "PACKAGES" ? "Kamida bitta paketni tanlang." : "Kamida bitta kursni tanlang.";
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
                : item.discount_type === "FREE_ACCESS" ? <>Bepul kirish · Free Access</>
                  : <>Premium · {item.discount_value} kun</>}
        </span>
      ),
    },
    {
      key: "products",
      header: "Kurs / paket",
      render: (item) => {
        const category = item.product_category ?? "COURSES";
        const selectedCourses = (products?.courses ?? []).filter((course) => item.applicable_course_ids.includes(course.id));
        const selectedPackages = (products?.packages ?? []).filter((pkg) => item.applicable_package_codes.includes(pkg.code));
        const labels = category === "MULTILEVEL" ? ["Modelltest 1–10"]
          : [...new Set(selectedCourses.map((course) => course.level)), ...selectedPackages.map((pkg) => pkg.label)];
        return (
          <div className="max-w-48" data-testid="promo-category" data-category={category}>
            <span className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-bold ${category === "MULTILEVEL" ? "bg-amber-500/15 text-amber-600" : "bg-[var(--admin-primary)]/10 text-[var(--admin-primary)]"}`}>
              {CATEGORY_LABEL[category]}
            </span>
            <span className="mt-0.5 block truncate text-xs" title={labels.join(", ") || "Premium"}>{labels.join(", ") || "Premium"}</span>
            {item.assigned_user_email && <span className="block truncate text-[11px] text-[var(--admin-text-muted)]" title={item.assigned_user_email}>Faqat: {item.assigned_user_email}</span>}
          </div>
        );
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
        const label: Record<string, string> = {
          ACTIVE: "Faol", SCHEDULED: "Rejalashtirilgan", EXPIRED: "Muddati tugagan", EXHAUSTED: "Limit tugagan", INACTIVE: "Nofaol",
          PENDING: "Tasdiqlash kutilmoqda", APPROVED: "Tasdiqlangan (faol emas)", REJECTED: "Rad etilgan", DISABLED: "O‘chirilgan",
        };
        const style = item.status === "ACTIVE" ? "text-[var(--admin-success)] bg-[var(--admin-success)]/10"
          : item.status === "SCHEDULED" || item.status === "APPROVED" ? "text-[var(--admin-primary)] bg-[var(--admin-primary)]/10"
            : item.status === "PENDING" ? "text-[var(--admin-warning)] bg-[var(--admin-warning)]/15"
              : item.status === "REJECTED" ? "text-[var(--admin-danger)] bg-[var(--admin-danger)]/10"
                : "text-[var(--admin-text-muted)] bg-white/5";
        return (
          <div className="flex flex-col items-start gap-1" data-testid="promo-status" data-status={item.status} data-approval={item.approval_status ?? ""}>
            <span className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${style}`}>{label[item.status] ?? item.status}</span>
            {item.approved_by_email && item.approval_status !== "PENDING" && (
              <span className="whitespace-nowrap text-[11px] text-[var(--admin-text-muted)]">Tasdiqlagan: {item.approved_by_email}</span>
            )}
            {item.requires_approval && (
              <span className="whitespace-nowrap rounded-full bg-[var(--admin-warning)]/15 px-2 py-0.5 text-[11px] font-semibold text-[var(--admin-warning)]">
                Tasdiq kerak{item.pending_requests ? ` · ${item.pending_requests} so‘rov` : ""}
              </span>
            )}
          </div>
        );
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
          {item.approval_status === "PENDING" && (
            <>
              <button type="button" title="Tasdiqlash va faollashtirish" aria-label={`${item.code} tasdiqlash`} data-testid="promo-approve" disabled={toggleMutation.isPending}
                onClick={() => review(item, "approve_activate")} className="rounded-lg p-2 text-[var(--admin-success)] hover:bg-[var(--admin-success)]/10"><ShieldCheck size={15} /></button>
              <button type="button" title="Rad etish" aria-label={`${item.code} rad etish`} data-testid="promo-reject" disabled={toggleMutation.isPending}
                onClick={() => review(item, "reject")} className="rounded-lg p-2 text-[var(--admin-danger)] hover:bg-[var(--admin-danger)]/10"><Ban size={15} /></button>
            </>
          )}
          {(item.approval_status === "APPROVED" || item.approval_status === "DISABLED") && (
            <button type="button" title="Faollashtirish" aria-label={`${item.code} faollashtirish`} data-testid="promo-activate" disabled={toggleMutation.isPending}
              onClick={() => review(item, "activate")} className="rounded-lg p-2 text-[var(--admin-text-secondary)] hover:bg-white/5"><Check size={15} /></button>
          )}
          {(item.approval_status === "ACTIVE" || item.approval_status === "APPROVED") && (
            <button type="button" title="O‘chirib qo‘yish" aria-label={`${item.code} deaktivatsiya`} data-testid="promo-disable" disabled={toggleMutation.isPending}
              onClick={() => review(item, "disable")} className="rounded-lg p-2 text-[var(--admin-text-secondary)] hover:bg-white/5"><X size={15} /></button>
          )}
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

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-8">
        {[
          { label: "Faol", value: counts.active, icon: Check },
          { label: "Tasdiqlash kutilmoqda", value: counts.pending, icon: Hourglass },
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
            <option value="ALL">Barcha holatlar</option><option value="PENDING">Tasdiqlash kutilmoqda</option><option value="APPROVED">Tasdiqlangan (faol emas)</option><option value="ACTIVE">Faol</option><option value="SCHEDULED">Rejalashtirilgan</option><option value="EXPIRED">Muddati tugagan</option><option value="DISABLED">O‘chirilgan</option><option value="REJECTED">Rad etilgan</option><option value="EXHAUSTED">Limit tugagan</option>
          </AdminSelect>
          <AdminSelect aria-label="Chegirma turi" value={typeFilter} onChange={(event) => { setTypeFilter(event.target.value); setPage(1); }}>
            <option value="ALL">Barcha chegirmalar</option><option value="PERCENT">Foizli chegirma</option><option value="SPECIAL_PRICE">Maxsus narx</option><option value="FIXED">Belgilangan summa</option><option value="FREE_DAYS">Premium kunlari</option><option value="FREE_ACCESS">Bepul taqdim etish</option>
          </AdminSelect>
          <AdminSelect aria-label="Kurs yoki paket" value={productFilter} onChange={(event) => { setProductFilter(event.target.value); setPage(1); }}>
            <option value="ALL">Barcha mahsulotlar</option>
            <option value="MULTILEVEL">Multilevel Modelltest Premium</option>
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
            <p className="rounded-lg bg-[var(--admin-warning)]/10 p-2.5 text-xs text-[var(--admin-text-secondary)]" data-testid="promo-approval-note">
              {editing
                ? "Chegirma turi, qiymati, kategoriya yoki mahsulotlar o‘zgarsa, kod yana «Tasdiqlash kutilmoqda» holatiga o‘tadi va qayta tasdiqlanmaguncha ishlamaydi."
                : "Yangi promokod «Tasdiqlash kutilmoqda» (PENDING) holatida yaratiladi: Super Admin jadvaldagi ✓ tugmasi bilan tasdiqlab faollashtirmaguncha hech qayerda ishlamaydi."}
            </p>
            {!isMultilevel && ["PERCENT", "FIXED", "SPECIAL_PRICE"].includes(form.discount_type) && (
              <label className="flex items-start gap-2 text-sm text-[var(--admin-text-secondary)]" data-testid="promo-requires-approval">
                <input type="checkbox" className="mt-1" checked={form.requires_approval} onChange={(event) => setForm({ ...form, requires_approval: event.target.checked })} />
                <span>
                  Admin tasdig‘i talab qilinsin (requires_approval)
                  <span className="block text-xs text-[var(--admin-text-muted)]">Talaba kodni kiritganda so‘rov yuboriladi; chegirma faqat “Promo-Freigaben” bo‘limida tasdiqlangandan keyin qo‘llanadi.</span>
                </span>
              </label>
            )}
          </section>
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Chegirma shartlari</h3>
          <div>
            <AdminLabel htmlFor="promo-category">Mahsulot kategoriyasi</AdminLabel>
            <AdminSelect
              id="promo-category"
              data-testid="promo-category-select"
              value={form.product_category}
              onChange={(e) => {
                const category = e.target.value as ProductCategory;
                const type = TYPES_BY_CATEGORY[category].includes(form.discount_type) ? form.discount_type : "PERCENT";
                setFieldErrors((current) => ({ ...current, scope: undefined }));
                setForm({ ...form, product_category: category, discount_type: type, discount_value: type === "FREE_ACCESS" ? 100 : form.discount_value,
                  applicable_course_ids: [], applicable_package_codes: [], requires_approval: category === "MULTILEVEL" ? false : form.requires_approval });
              }}
            >
              <option value="COURSES">Kurslar (A1, A2, B1 …)</option>
              <option value="PACKAGES">Paketlar (A1 → B1 …)</option>
              <option value="MULTILEVEL">Multilevel Modelltest (10 ta Modelltest Premium)</option>
            </AdminSelect>
            <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Kurs kodi Multilevel uchun, Multilevel kodi kurslar uchun ishlamaydi.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel htmlFor="promo-type">Chegirma turi</AdminLabel>
              <AdminSelect
                id="promo-type"
                value={form.discount_type}
                onChange={(e) => setForm({ ...form, discount_type: e.target.value, discount_value: e.target.value === "FREE_ACCESS" ? 100 : form.discount_type === "FREE_ACCESS" ? 1 : form.discount_value, applicable_course_ids: e.target.value === "FREE_DAYS" ? [] : form.applicable_course_ids, applicable_package_codes: e.target.value === "FREE_DAYS" ? [] : form.applicable_package_codes })}
              >
                {TYPES_BY_CATEGORY[form.product_category].map((type) => <option key={type} value={type}>{TYPE_LABEL[type]}</option>)}
              </AdminSelect>
            </div>
            {isFreeAccess ? (
              <p className="self-end rounded-lg bg-[var(--admin-primary)]/10 p-2 text-xs text-[var(--admin-text-secondary)]" data-testid="free-access-note">
                {isMultilevel
                  ? "Bu promo kod barcha 10 ta Multilevel Modelltestni bepul ochadi (karta orqali to‘lov talab qilinmaydi)."
                  : "Bu promo kod tegishli kursga bepul kirish beradi. To‘lov summasi 0 bo‘ladi; chegirma qiymati kerak emas."}
              </p>
            ) : (
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
            )}
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

          {isMultilevel && (
            <p className="rounded-lg bg-amber-500/10 p-3 text-xs text-[var(--admin-text-secondary)]" data-testid="promo-multilevel-scope">
              Mahsulot: <strong>{products?.multilevel?.label ?? "VIZU Multilevel Modelltest Premium"}</strong> — Modelltest 1–10, muddatsiz
              {products?.multilevel ? ` · narx ${new Intl.NumberFormat("de-DE").format(products.multilevel.price)} so‘m` : ""}.
            </p>
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
                                    applicable_course_ids: form.product_category === "COURSES" ? (products?.courses ?? []).map((course) => course.id) : [],
                                    applicable_package_codes: form.product_category === "PACKAGES" ? (products?.packages ?? []).map((product) => product.code) : [],
                                  });
                                }}
                  >Barchasini tanlash</button>
                </div>
                <p className="text-xs text-[var(--admin-text-muted)]">Faqat belgilangan {form.product_category === "PACKAGES" ? "paketlarga" : "kurslarga"} qo‘llanadi. Bo‘sh scope barcha mahsulotlarni anglatmaydi.</p>
                {form.product_category === "COURSES" && (
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
                )}
              </div>
              {form.product_category === "PACKAGES" && (
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
              )}
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
            {details.created_by_email && <p className="text-xs text-[var(--admin-text-muted)]">Yaratgan: {details.created_by_email}</p>}
            <p className="text-xs text-[var(--admin-text-muted)]" data-testid="promo-approval-info">
              Tasdiqlash: {details.approval_status ?? "—"}
              {details.approved_at ? ` · ${new Date(details.approved_at).toLocaleString("uz-UZ")}` : ""}
              {details.approved_by_email ? ` · ${details.approved_by_email}` : ""}
              {details.review_note ? ` · ${details.review_note}` : ""}
            </p>
            <div className="grid gap-2 sm:grid-cols-2" data-testid="promo-history-filters">
              <AdminInput placeholder="Foydalanuvchi (e-mail / login)" value={detailSearch} onChange={(e) => { setDetailSearch(e.target.value); setDetailPage(1); }} />
              <AdminSelect value={detailPlan} onChange={(e) => { setDetailPlan(e.target.value); setDetailPage(1); }} aria-label="Paket">
                <option value="">Barcha paketlar</option>
                <option value="ML_PREMIUM">Multilevel Modelltest Premium</option>
                {["A1", "A2", "B1", "B2", "C1"].map((lv) => <option key={lv} value={lv}>{lv}</option>)}
                {(products?.packages ?? []).map((pkg) => <option key={pkg.code} value={pkg.code}>{pkg.label}</option>)}
              </AdminSelect>
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
      <AdminPageHeader title="Payments"
        description="Übersicht, Zahlungsanfragen, Kurs- und Multilevel-Modelltest-Zahlungen, Promo-Codes mit Freigabe, Promo-Anfragen, Kaufhistorie und Einstellungen." />
      <DateFilterBar filter={dateFilter} onChange={setDateFilter} />
      <AdminTabs
        defaultValue="overview"
        tabs={[
          { value: "overview", label: "Overview", content: <PaymentsOverviewTab /> },
          { value: "new-buyers", label: "Payment Requests", content: <NewBuyersSection dateFilter={dateFilter} /> },
          { value: "course-payments", label: "Course Payments", content: <NewBuyersSection dateFilter={dateFilter} kind="course" /> },
          {
            value: "multilevel-payments", label: "Multilevel Modelltest Payments",
            content: (
              <div className="space-y-8" data-testid="multilevel-payments-tab">
                <NewBuyersSection dateFilter={dateFilter} kind="multilevel" />
                <MlEntitlementsList />
              </div>
            ),
          },
          { value: "promos", label: "Promo Codes", content: <PromoCodesTab /> },
          { value: "promo-requests", label: "Promo Requests", content: <PromoRequestsTab /> },
          { value: "history", label: "Purchase History", content: <OrdersHistoryTab dateFilter={dateFilter} /> },
          { value: "settings", label: "Payment Settings", content: <PaymentSettingsTab /> },
        ]}
      />
    </div>
  );
}
