"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Wifi, WifiOff } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

/** A connection that drops while a page is open: a clear banner instead of failing requests, nothing is reloaded and the
 * login stays. When the network is back the page's data is fetched again (no full reload, so typed answers stay). */
export default function NetworkStatus() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [state, setState] = useState<"online" | "offline" | "back">("online");

  useEffect(() => {
    let timer = 0;
    const offline = () => {
      window.clearTimeout(timer);
      setState("offline");
    };
    const online = () => {
      setState((s) => (s === "offline" ? "back" : s));
      void queryClient.invalidateQueries();
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setState("online"), 2500);
    };
    if (typeof navigator !== "undefined" && navigator.onLine === false) offline();
    window.addEventListener("offline", offline);
    window.addEventListener("online", online);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("offline", offline);
      window.removeEventListener("online", online);
    };
  }, [queryClient]);

  if (state === "online") return null;
  const off = state === "offline";
  return (
    <div role="status" aria-live="polite" data-testid={off ? "network-offline" : "network-back"}
         className={`safe-top fixed inset-x-0 top-0 z-[90] flex items-center justify-center gap-2 px-4 py-2 text-center text-sm font-medium text-white shadow-md ${off ? "bg-[#0e1834]" : "bg-emerald-700"}`}>
      {off ? <WifiOff size={16} aria-hidden="true" className="shrink-0 text-[#d4af37]" /> : <Wifi size={16} aria-hidden="true" className="shrink-0" />}
      <span>{off ? t("mobileApp.offlineBanner") : t("mobileApp.onlineAgain")}</span>
    </div>
  );
}
