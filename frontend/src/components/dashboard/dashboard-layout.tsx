"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import Header from "./header";
import Sidebar from "./sidebar";
import MobileNav from "./mobile-nav";
import PageTransition from "@/components/motion/page-transition";
import GlobalChatWidget from "@/features/global-chat/components/global-chat-widget";
import { cn } from "@/lib/utils";

interface Props {
  children: ReactNode;
}

export default function DashboardLayout({ children }: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  // VIZU LMS pages learn on a white surface (light theme; see .lms-theme)
  const pathname = usePathname() ?? "";
  const lms = /^\/(kurse|lektion)(\/|$)/.test(pathname);

  return (
    <div className={cn("flex min-h-screen bg-surface-bg", lms && "lms-theme")} data-lms={lms || undefined}>
      <Sidebar />
      <MobileNav open={mobileNavOpen} onOpenChange={setMobileNavOpen} />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header onMenuClick={() => setMobileNavOpen(true)} />

        <main className="relative flex-1 overflow-x-hidden overflow-y-auto">
          {!lms && <div className="pointer-events-none absolute -right-40 -top-40 h-[480px] w-[480px] rounded-full bg-accent-gold/[0.08] blur-3xl dark:bg-accent-blue/[0.08]" />}

          {/* pb-24: the end of every page can scroll clear of the Global Chat button */}
          <section className="relative z-10 mx-auto w-full max-w-[1440px] px-4 pb-24 pt-6 sm:px-6 lg:px-8 lg:pb-24 lg:pt-8">
            <PageTransition>{children}</PageTransition>
          </section>
        </main>
      </div>

      <GlobalChatWidget />
    </div>
  );
}
