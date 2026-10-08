"use client";

import { useQuery } from "@tanstack/react-query";

import { useTranslation } from "@/lib/i18n/use-translation";
import { getActiveAdvertisements } from "@/features/advertisements/advertisement";

import AdvertisementBannerView from "./advertisement-banner-view";
import AdvertisementCarousel from "./advertisement-carousel";

/** Dashboard top: the admin-managed Werbung-Banner. Every eligible
 * advertisement rotates in AdvertisementCarousel (7 s each, glass-shatter
 * transition); a single advertisement is simply shown. Impressions are sent
 * only while a banner is really visible, at most once per advertisement per
 * page visit; clicks go through the backend tracking redirect. Without an
 * active advertisement a neutral VIZU Academy banner is shown (no fake ad). */
export default function AdvertisementBanner() {
  const { t } = useTranslation();
  const { data: ads, isLoading } = useQuery({
    queryKey: ["dashboard-active-advertisements"],
    queryFn: getActiveAdvertisements,
    staleTime: 60_000,
  });

  if (isLoading) {
    return <div className="h-[220px] animate-pulse rounded-[22px] bg-surface-card ring-1 ring-surface-border motion-reduce:animate-none" />;
  }

  if (!ads || ads.length === 0) {
    return (
      <AdvertisementBannerView
        title={t("dashboard.adFallbackTitle")}
        description={t("dashboard.adFallbackBody")}
        ctaText={t("dashboard.adFallbackCta")}
        href="/courses"
      />
    );
  }

  return <AdvertisementCarousel ads={ads} />;
}
