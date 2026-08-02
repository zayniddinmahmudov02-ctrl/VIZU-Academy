"use client";

import { ReactNode } from "react";
import { Tabs } from "@base-ui/react/tabs";

export interface AdminTab {
  value: string;
  label: string;
  content: ReactNode;
}

export default function AdminTabs({ tabs, defaultValue }: { tabs: AdminTab[]; defaultValue: string }) {
  return (
    <Tabs.Root defaultValue={defaultValue}>
      <Tabs.List className="mb-6 flex flex-wrap gap-1 overflow-x-auto rounded-xl bg-[var(--admin-card)] p-1.5 ring-1 ring-[var(--admin-border)]">
        {tabs.map((tab) => (
          <Tabs.Tab
            key={tab.value}
            value={tab.value}
            className="whitespace-nowrap rounded-lg px-3.5 py-2 text-sm font-medium text-[var(--admin-text-secondary)] transition-colors data-[selected]:bg-[var(--admin-primary)] data-[selected]:text-white"
          >
            {tab.label}
          </Tabs.Tab>
        ))}
      </Tabs.List>

      {tabs.map((tab) => (
        <Tabs.Panel key={tab.value} value={tab.value}>
          {tab.content}
        </Tabs.Panel>
      ))}
    </Tabs.Root>
  );
}
