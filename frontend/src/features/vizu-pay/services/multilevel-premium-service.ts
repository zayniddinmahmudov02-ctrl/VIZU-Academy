import { isAxiosError } from "axios";

import { api } from "@/services/api";

/** Multilevel Modelltest Premium (backend services/vizu_pay/multilevel_premium.py). Prices and amounts always come from the server. */

export interface MlProduct {
  code: string;
  label: string;
  price: number;
  currency: string;
  status: "ACTIVE" | "DISABLED";
  purchasable: boolean;
  unlimited: boolean;
}

export interface MlOrder {
  id: string;
  status: string;
  final_amount: number;
  base_amount: number;
  discount_amount: number;
  promo_code: string | null;
  no_receipt: boolean;
  has_proof: boolean;
  paid_at: string | null;
  created_at: string;
}

export interface MlStatus {
  product: MlProduct;
  cards: { label: string; number: string }[];
  entitled: boolean;
  staff: boolean;
  entitlement: { source: "PAYMENT" | "PROMO"; granted_at: string } | null;
  pending_order: MlOrder | null;
  last_rejected: { reason: string | null; reviewed_at: string | null } | null;
  blocked: boolean;
  tests: { total: number; available: number };
}

export interface MlQuote {
  base_amount: number;
  promo_discount: number;
  final_amount: number;
  promo_error: string | null;
  free: boolean;
}

export async function getMlStatus(): Promise<MlStatus> {
  return (await api.get<MlStatus>("/api/v1/vizu-pay/multilevel")).data;
}

export async function getMlQuote(promoCode?: string): Promise<MlQuote> {
  return (await api.get<MlQuote>("/api/v1/vizu-pay/multilevel/quote", { params: promoCode ? { promo_code: promoCode } : {} })).data;
}

export interface MlOrderInput {
  promoCode?: string;
  noReceipt: boolean;
  receipt?: File | null;
  paidDate?: string;
  paidTime?: string;
  note?: string;
}

/** Multipart: no amount is ever sent — the server computes it. */
export async function createMlOrder(input: MlOrderInput): Promise<MlOrder> {
  const form = new FormData();
  if (input.promoCode) form.append("promo_code", input.promoCode);
  form.append("no_receipt", input.noReceipt ? "true" : "false");
  if (!input.noReceipt && input.receipt) form.append("proof", input.receipt);
  if (input.paidDate) form.append("paid_date", input.paidDate);
  if (input.paidTime) form.append("paid_time", input.paidTime);
  if (input.note?.trim()) form.append("note", input.note.trim());
  return (await api.post<MlOrder>("/api/v1/vizu-pay/multilevel/orders", form, { headers: { "Content-Type": "multipart/form-data" } })).data;
}

export async function redeemMlPromo(code: string): Promise<MlStatus> {
  return (await api.post<MlStatus>("/api/v1/vizu-pay/multilevel/redeem", { code })).data;
}

/** The server's error code ("PROMO_NOT_ACTIVE", "RECEIPT_REQUIRED", …) or its text, for mlErrorKey. */
export function apiCode(err: unknown): string | null {
  if (!isAxiosError<{ message?: string; detail?: string }>(err)) return null;
  const raw = err.response?.data?.message ?? err.response?.data?.detail;
  return typeof raw === "string" ? raw : null;
}

const CODE_KEYS = [
  "PROMO_NOT_ACTIVE", "PROMO_WRONG_PRODUCT", "PROMO_FREE_USE_REDEEM", "RECEIPT_REQUIRED", "PAID_AT_REQUIRED", "PAID_AT_INVALID",
  "PAID_AT_INCOMPLETE", "PAYMENT_REQUEST_ALREADY_PENDING", "ALREADY_ENTITLED", "PRODUCT_NOT_AVAILABLE", "PAYMENT_REQUEST_BLOCKED",
];

/** Maps a server message to a `mlPremium.*` translation key (the server answers in English or with UPPER_SNAKE codes). */
export function mlErrorKey(message: string | null | undefined): string {
  if (!message) return "mlPremium.errGeneric";
  const code = message.split(":")[0].trim();
  if (code === "PAID_AT_INCOMPLETE") return "mlPremium.errPAID_AT_REQUIRED";
  if (CODE_KEYS.includes(code)) return `mlPremium.err${code}`;
  const text = message.toLowerCase();
  if (text.includes("not found")) return "mlPremium.errNOT_FOUND";
  if (text.includes("expired")) return "mlPremium.errEXPIRED";
  if (text.includes("not active yet")) return "mlPremium.errNOT_YET";
  if (text.includes("limit")) return "mlPremium.errLIMIT";
  if (text.includes("too large")) return "mlPremium.fileTooLarge";
  if (text.includes("doesn't match") || text.includes("unsupported proof")) return "mlPremium.fileType";
  return "mlPremium.errGeneric";
}
