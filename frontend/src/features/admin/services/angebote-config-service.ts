import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";

/** Level settings of Admin -> Angebote (app_settings "angebote"); packages are managed separately below. */
export interface AngeboteConfig {
  levels: Record<string, boolean>;
  /** lesson-access gate per level ("Verkauf"): when off, paid lessons open only for buyers of that level */
  sales: Record<string, boolean>;
  free_lessons: number;
  defaults: { levels: Record<string, boolean>; sales: Record<string, boolean>; free_lessons: number };
}

export interface AngeboteConfigInput {
  levels: Record<string, boolean>;
  sales: Record<string, boolean>;
  free_lessons: number;
}

export async function getAngeboteConfig(): Promise<AngeboteConfig> {
  return (await api.get<AngeboteConfig>(`${ADMIN_ENDPOINTS.adminVizuPay}/angebote-config`)).data;
}

export async function saveAngeboteConfig(input: AngeboteConfigInput): Promise<AngeboteConfig> {
  return (await api.put<AngeboteConfig>(`${ADMIN_ENDPOINTS.adminVizuPay}/angebote-config`, input)).data;
}

// ── course packages (table course_packages; backend services/vizu_pay/packages.py) ──

export type PackageStatus = "ACTIVE" | "COMING_SOON" | "DISABLED";

export interface CoursePackage {
  code: string;
  name: string;
  package_type: "LEVEL" | "PACKAGE";
  included_levels: string[];
  price: number | null;
  original_price: number | null;
  discount_percent: number | null;
  duration_days: number;
  status: PackageStatus;
  description: Record<string, string>;
  sort_order: number;
  purchasable: boolean;
  approved_orders: number;
  pending_orders: number;
  updated_at: string;
}

export type PackageInput = Partial<Omit<CoursePackage, "purchasable" | "approved_orders" | "pending_orders" | "updated_at">>;

export async function listPackages(): Promise<CoursePackage[]> {
  return (await api.get<CoursePackage[]>(`${ADMIN_ENDPOINTS.adminVizuPay}/packages`)).data;
}

export async function createPackage(input: PackageInput): Promise<CoursePackage> {
  return (await api.post<CoursePackage>(`${ADMIN_ENDPOINTS.adminVizuPay}/packages`, input)).data;
}

export async function updatePackage(code: string, input: PackageInput): Promise<CoursePackage> {
  return (await api.put<CoursePackage>(`${ADMIN_ENDPOINTS.adminVizuPay}/packages/${code}`, input)).data;
}
