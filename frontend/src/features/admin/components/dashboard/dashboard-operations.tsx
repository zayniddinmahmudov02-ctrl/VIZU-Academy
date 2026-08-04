"use client";

import {
  BookOpen,
  Brain,
  Clock,
  CreditCard,
  Crown,
  FileText,
  FolderOpen,
  Gauge,
  Globe,
  Headphones,
  HelpCircle,
  Layers3,
  Mic,
  PenLine,
  RotateCcw,
  Sparkles,
  SpellCheck,
  Video,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import type { AIStats, ContentCounts, PaymentsSummary } from "@/features/admin/types/enterprise-dashboard.types";

function formatCurrency(value: number): string {
  return `${value.toLocaleString("de-DE")} UZS`;
}

function StatTile({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-white/[0.02] p-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <p className="truncate text-sm font-bold text-[var(--admin-text-primary)]">{value}</p>
        <p className="truncate text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</p>
      </div>
    </div>
  );
}

export function OperationsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {[0, 1, 2].map((i) => (
        <AdminCard key={i} className="h-[220px] animate-pulse">
          <div className="h-3 w-24 rounded bg-white/5" />
          <div className="mt-6 grid grid-cols-2 gap-2">
            {[0, 1, 2, 3].map((j) => (
              <div key={j} className="h-12 rounded-lg bg-white/5" />
            ))}
          </div>
        </AdminCard>
      ))}
    </div>
  );
}

function PaymentsPanel({ payments }: { payments: PaymentsSummary }) {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Payments</h3>
      <div className="grid grid-cols-2 gap-2">
        <StatTile icon={Wallet} label="Today" value={formatCurrency(payments.today_revenue)} />
        <StatTile icon={Wallet} label="This Week" value={formatCurrency(payments.week_revenue)} />
        <StatTile icon={Wallet} label="This Month" value={formatCurrency(payments.month_revenue)} />
        <StatTile icon={Clock} label="Pending" value={payments.pending_payments} />
        <StatTile icon={RotateCcw} label="Refunds" value={payments.refunds} />
        <StatTile icon={Crown} label="Premium Sales" value={payments.premium_sales} />
      </div>
    </AdminCard>
  );
}

const CONTENT_DEFS: { key: keyof ContentCounts; label: string; icon: LucideIcon }[] = [
  { key: "languages", label: "Languages", icon: Globe },
  { key: "levels", label: "Levels", icon: Gauge },
  { key: "modules", label: "Modules", icon: Layers3 },
  { key: "lessons", label: "Lessons", icon: BookOpen },
  { key: "videos", label: "Videos", icon: Video },
  { key: "vocabulary", label: "Vocabulary", icon: SpellCheck },
  { key: "grammar", label: "Grammar", icon: FileText },
  { key: "reading", label: "Reading", icon: BookOpen },
  { key: "listening", label: "Listening", icon: Headphones },
  { key: "writing", label: "Writing", icon: PenLine },
  { key: "speaking", label: "Speaking", icon: Mic },
  { key: "homework", label: "Homework", icon: FolderOpen },
  { key: "quiz", label: "Quiz", icon: HelpCircle },
  { key: "mock_tests", label: "Mock Tests", icon: CreditCard },
];

function ContentPanel({ content }: { content: ContentCounts }) {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Content</h3>
      <div className="grid grid-cols-2 gap-2">
        {CONTENT_DEFS.map((def) => (
          <StatTile key={def.key} icon={def.icon} label={def.label} value={content[def.key]} />
        ))}
      </div>
    </AdminCard>
  );
}

function AiPanel({ ai }: { ai: AIStats }) {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">AI</h3>
      <div className="grid grid-cols-2 gap-2">
        <StatTile icon={PenLine} label="Writing Checked Today" value={ai.writing_checked_today} />
        <StatTile icon={Mic} label="Speaking Checked Today" value={ai.speaking_checked_today} />
        <StatTile icon={Clock} label="Pending AI Reviews" value={ai.pending_ai_reviews} />
        <StatTile
          icon={Sparkles}
          label="Average AI Score"
          value={ai.average_ai_score !== null ? `${ai.average_ai_score}%` : "—"}
        />
      </div>
      {ai.pending_ai_reviews === 0 && ai.writing_checked_today === 0 && ai.speaking_checked_today === 0 && (
        <p className="mt-3 flex items-center gap-1.5 text-xs text-[var(--admin-text-muted)]">
          <Brain size={13} />
          Noch keine KI-Bewertungen durchgeführt.
        </p>
      )}
    </AdminCard>
  );
}

export default function DashboardOperations({
  payments,
  content,
  ai,
}: {
  payments: PaymentsSummary;
  content: ContentCounts;
  ai: AIStats;
}) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <PaymentsPanel payments={payments} />
      <ContentPanel content={content} />
      <AiPanel ai={ai} />
    </div>
  );
}
