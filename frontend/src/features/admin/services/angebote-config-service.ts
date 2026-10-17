import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";

export interface AngeboteOffer {
  code: string;
  kind: "LEVEL" | "PACKAGE";
  label: string;
  levels: string[];
  available_levels: string[];
  original_price: number | null;
  sale_price: number | null;
  discount_percent: number | null;
  active: boolean;
  purchasable: boolean;
  free_lessons: number;
  currency: string;
}

export interface OfferOverride {
  original_price?: number | null;
  sale_price?: number | null;
  discount_percent?: number | null;
  active?: boolean;
  levels?: string[];
}

export interface AngeboteConfig {
  offers: AngeboteOffer[];
  levels: Record<string, boolean>;
  free_lessons: number;
  defaults: { offers: Record<string, OfferOverride>; levels: Record<string, boolean>; free_lessons: number };
}

export interface AngeboteConfigInput {
  offers: Record<string, OfferOverride>;
  levels: Record<string, boolean>;
  free_lessons: number;
}

export async function getAngeboteConfig(): Promise<AngeboteConfig> {
  return (await api.get<AngeboteConfig>(`${ADMIN_ENDPOINTS.adminVizuPay}/angebote-config`)).data;
}

export async function saveAngeboteConfig(input: AngeboteConfigInput): Promise<AngeboteConfig> {
  return (await api.put<AngeboteConfig>(`${ADMIN_ENDPOINTS.adminVizuPay}/angebote-config`, input)).data;
}
