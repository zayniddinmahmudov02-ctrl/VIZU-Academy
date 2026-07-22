export interface AdminOrderItem {
  id: string;
  plan: string;
  planLabel: string;
  durationDays: number;
  baseAmount: number;
  discountAmount: number;
  finalAmount: number;
  currency: string;
  paymentMethod: string;
  status: string;
  proofUrl: string | null;
  proofType: string | null;
  promoCode: string | null;
  rejectionReason: string | null;
  expiresAt: string | null;
  reviewedAt: string | null;
  createdAt: string;
  userId: string;
  userEmail: string;
  userUsername: string;
  reviewedByEmail: string | null;
}

export interface AdminOrderListResponse {
  items: AdminOrderItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface PromoCodeItem {
  id: string;
  code: string;
  campaign: string | null;
  discountType: "PERCENT" | "FIXED";
  discountValue: number;
  maxUses: number | null;
  usedCount: number;
  expiresAt: string | null;
  isActive: boolean;
  createdAt: string;
}

export interface RevenueChartPoint {
  label: string;
  value: number;
}

export interface PlanBreakdown {
  plan: string;
  label: string;
  orders: number;
  revenue: number;
}

export interface MethodBreakdown {
  method: string;
  orders: number;
  revenue: number;
}

export interface StatusBreakdown {
  status: string;
  count: number;
}

export interface RevenueOverview {
  totalRevenue: number;
  revenueThisMonth: number;
  revenueToday: number;
  totalOrders: number;
  pendingOrders: number;
  trialsStarted: number;
  trialsConverted: number;
  trialConversionRate: number;
  monthlyRevenueChart: RevenueChartPoint[];
  planBreakdown: PlanBreakdown[];
  methodBreakdown: MethodBreakdown[];
  statusBreakdown: StatusBreakdown[];
}

export interface PaymentLogItem {
  id: string;
  actorEmail: string | null;
  action: string;
  details: string | null;
  ipAddress: string | null;
  createdAt: string;
}

export interface PaymentLogResponse {
  items: PaymentLogItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
