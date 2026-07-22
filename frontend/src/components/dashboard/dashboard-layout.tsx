"use client";

import { useState } from "react";
import type { ReactNode } from "react";

import Header from "./header";
import Sidebar from "./sidebar";
import MobileNav from "./mobile-nav";
import PageTransition from "@/components/motion/page-transition";

interface Props {
  children: ReactNode;
}

export default function DashboardLayout({ children }: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-surface-bg">
      <Sidebar />
      <MobileNav open={mobileNavOpen} onOpenChange={setMobileNavOpen} />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header onMenuClick={() => setMobileNavOpen(true)} />

        <main className="relative flex-1 overflow-x-hidden overflow-y-auto">
          <div className="pointer-events-none absolute -right-40 -top-40 h-[480px] w-[480px] rounded-full bg-accent-gold/[0.08] blur-3xl dark:bg-accent-blue/[0.08]" />

          <section className="relative z-10 mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            <PageTransition>{children}</PageTransition>
          </section>
        </main>
      </div>
    </div>
  );
}
