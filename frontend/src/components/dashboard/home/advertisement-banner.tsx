"use client";

import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";

import { useTranslation } from "@/lib/i18n/use-translation";
import {
  advertisementClickUrl,
  getActiveAdvertisement,
  trackAdvertisementImpression,
} from "@/features/advertisements/advertisement";

import AdvertisementBannerView from "./advertisement-banner-view";

/** Dashboard top: the admin-managed Werbung-Banner. An impression is sent
 * only once the banner is really visible (IntersectionObserver, >= 50 %),
 * and at most once per advertisement per page visit — re-renders never
 * count. The click goes through the backend tracking redirect. Without an
 * active advertisement a neutral VIZU Academy banner is shown (no fake ad). */
export default function AdvertisementBanner() {
  const { t } = useTranslation();
  const { data: ad, isLoading } = useQuery({
    queryKey: ["dashboard-active-advertisement"],
    queryFn: getActiveAdvertisement,
    staleTime: 60_000,
  });

  const ref = useRef<HTMLAnchorElement>(null);
  const trackedId = useRef<string | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!ad || !node || trackedId.current === ad.id) return;
    if (typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting) && trackedId.current !== ad.id) {
          trackedId.current = ad.id;
          observer.disconnect();
          void trackAdvertisementImpression(ad.id).catch(() => {
            /* analytics must never break the dashboard */
          });
        }
      },
      { threshold: 0.5 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [ad]);

  if (isLoading) {
    return <div className="h-[220px] animate-pulse rounded-[22px] bg-surface-card ring-1 ring-surface-border motion-reduce:animate-none" />;
  }

  if (!ad) {
    return (
      <AdvertisementBannerView
        title={t("dashboard.adFallbackTitle")}
        description={t("dashboard.adFallbackBody")}
        ctaText={t("dashboard.adFallbackCta")}
        href="/courses"
      />
    );
  }

  return (
    <AdvertisementBannerView
      ref={ref}
      title={ad.title}
      description={ad.description}
      imageUrl={ad.image_url}
      ctaText={ad.cta_text}
      href={advertisementClickUrl(ad)}
      external
    />
  );
}
