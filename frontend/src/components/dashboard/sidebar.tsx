"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";

import Logo from "@/components/common/logo";
import LanguageSwitcher from "./languages/language-switcher";
import { useHasMounted, useStoredBoolean } from "@/hooks/use-mounted";
import { useSidebarItems } from "@/hooks/use-sidebar-items";
import { useTranslation } from "@/lib/i18n/use-translation";
import NavItem from "../navigation/nav-item";

const STORAGE_KEY = "vizu-sidebar-collapsed";

export default function Sidebar() {
  const ready = useHasMounted();
  const storedCollapsed = useStoredBoolean(STORAGE_KEY);
  const [override, setOverride] = useState<boolean | null>(null);
  const collapsed = override ?? storedCollapsed;
  const { t } = useTranslation();
  const sidebarItems = useSidebarItems();

  function toggle() {
    const next = !collapsed;
    localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
    setOverride(next);
  }

  return (
    <motion.aside
      animate={{ width: collapsed ? 80 : 270 }}
      transition={{ duration: ready ? 0.25 : 0, ease: "easeOut" }}
      className="sticky top-0 z-30 hidden h-screen shrink-0 lg:block"
    >
      <div className="relative flex h-full flex-col p-4">
        <div className="pattern-accent-corner relative flex h-full flex-col overflow-hidden rounded-card bg-surface-sidebar shadow-[var(--shadow-card)] ring-1 ring-accent-gold/15">
          {/* Logo */}
          <div
            className={`relative z-10 flex items-center border-b border-white/10 ${
              collapsed ? "h-20 justify-center px-2" : "flex-col justify-center gap-2 px-5 py-6"
            }`}
          >
            <Logo
              size={collapsed ? 36 : 46}
              showText={!collapsed}
              orientation={collapsed ? "row" : "stack"}
              dark
              tagline
            />
          </div>

          {/* Navigation */}
          <nav className="relative z-10 space-y-1 overflow-y-auto overflow-x-hidden px-3 py-5">
            {sidebarItems.map((item) => (
              <NavItem key={item.href} {...item} collapsed={collapsed} />
            ))}
          </nav>

          {/* Collapse toggle */}
          <button
            onClick={toggle}
            aria-label={collapsed ? t("sidebar.expand") : t("sidebar.collapse")}
            className="absolute -right-3 top-24 z-20 flex h-7 w-7 items-center justify-center rounded-full bg-surface-card text-text-secondary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:text-accent-blue"
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>

          {/* Brand card — mini replica of the header lockup, sits directly below the nav */}
          <div
            className={`relative z-10 border-t border-white/10 px-3.5 pt-3.5 ${
              collapsed ? "mt-auto" : "mt-5"
            }`}
          >
            <div
              className={`flex flex-col items-center gap-2 rounded-2xl border border-accent-gold/30 bg-gradient-to-b from-white/[0.05] to-transparent py-4 shadow-[var(--shadow-3d-soft)] ${
                collapsed ? "px-0" : "px-3"
              }`}
            >
              <Logo size={collapsed ? 28 : 36} showText={false} />
              {!collapsed && (
                <div className="text-center">
                  <p className="text-xs font-extrabold leading-tight tracking-tight">
                    <span className="text-white">VIZU</span> <span className="text-accent-gold">ACADEMY</span>
                  </p>
                  <p className="mt-0.5 text-[9px] font-medium uppercase tracking-wide text-sidebar-muted/70">
                    © {new Date().getFullYear()}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Language switcher — fixed to the bottom of the sidebar */}
          {!collapsed && (
            <div className="relative z-10 mt-auto border-t border-white/10 p-3.5">
              <LanguageSwitcher variant="sidebar" />
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
