"use client";

import { useState } from "react";

import GlobalChatWidget from "@/features/global-chat/components/global-chat-widget";

import AdminGuard from "./admin-guard";
import AdminHeader from "./admin-header";
import AdminMobileNav from "./admin-mobile-nav";
import AdminSidebar from "./admin-sidebar";

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <AdminGuard>
      <div className="admin-shell flex min-h-screen">
        <div className="sticky top-0 hidden h-screen shrink-0 border-r border-[var(--admin-border)] lg:block">
          <AdminSidebar />
        </div>

        <AdminMobileNav open={mobileNavOpen} onOpenChange={setMobileNavOpen} />

        <div className="flex min-w-0 flex-1 flex-col">
          <AdminHeader onMenuClick={() => setMobileNavOpen(true)} />
          <main className="flex-1 p-4 pb-24 sm:p-6 sm:pb-24 lg:p-8 lg:pb-24">{children}</main>
        </div>
        <GlobalChatWidget />
      </div>
    </AdminGuard>
  );
}
