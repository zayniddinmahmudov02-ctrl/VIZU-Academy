import {
  Bell,
  BookOpenCheck,
  LifeBuoy,
  Award,
  BookOpen,
  Contact,
  CreditCard,
  Crown,
  FlaskConical,
  Layers,
  KeyRound,
  Globe,
  LayoutDashboard,
  Medal,
  Megaphone,
  MessagesSquare,
  Clapperboard,
  PanelsTopLeft,
  School,
  Settings,
  ShieldCheck,
  Tag,
  TrendingUp,
  Users,
  UsersRound,
  type LucideIcon,
} from "lucide-react";

export interface AdminNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** shown indented under the item above it (e.g. Lösung under LMS A1–C1) */
  child?: boolean;
}

export interface AdminNavGroup {
  items: AdminNavItem[];
}

// The sidebar exposes only top-level sections. A lesson's own content
// (Videokurs, Hören Audio, Schreiben / Sprechen Aufgaben) is managed
// through Kurse (LMS) -> Level -> Lesson. There are no test/quiz/vocabulary/
// grammar creators or generators, and no Schreiben/Sprechen grading in
// the admin panel: that content is produced externally (Claude) and
// imported into the database, and student submissions are reviewed in
// the Teacher Panel.
export const ADMIN_NAV_GROUPS: AdminNavGroup[] = [
  {
    items: [
      { label: "Dashboard", href: "/admin", icon: LayoutDashboard },
      { label: "Werbung-Banner", href: "/admin/werbung-banner", icon: Megaphone },
      { label: "Notifications", href: "/admin/notifications", icon: Bell },
      { label: "Support / Hilfeanfragen", href: "/admin/support", icon: LifeBuoy },
      { label: "Global Chat", href: "/admin/global-chat", icon: MessagesSquare },
      { label: "Languages", href: "/admin/languages", icon: Globe },
      { label: "Kurse (LMS)", href: "/admin/kurse", icon: BookOpenCheck },
      { label: "LMS A1–C1", href: "/admin/lms", icon: Layers },
      { label: "Lösung", href: "/admin/lms/loesung", icon: KeyRound, child: true },
      { label: "Media Management", href: "/admin/media-management", icon: Clapperboard },
      { label: "Vorbereitung", href: "/admin/mock-exams", icon: ShieldCheck },
      { label: "VIZU-Multilevel", href: "/admin/vizu-multilevel", icon: FlaskConical },
      { label: "Users", href: "/admin/users", icon: Users },
      { label: "Team", href: "/admin/team", icon: Contact },
      { label: "Lehrer-Zuweisungen", href: "/admin/teacher-assignments", icon: School },
      { label: "Gruppen / Guruhlar", href: "/admin/groups", icon: UsersRound },
      { label: "Premium-Users", href: "/admin/premium-users", icon: Crown },
      { label: "Zertifikate", href: "/admin/certificates", icon: Award },
      { label: "Achievements / Medals", href: "/admin/achievements", icon: Medal },
      { label: "Bücher", href: "/admin/books", icon: BookOpen },
      { label: "Payments", href: "/admin/payments", icon: CreditCard },
      { label: "Angebote & Preise", href: "/admin/angebote", icon: Tag },
      { label: "Analytics", href: "/admin/analytics", icon: TrendingUp },
      { label: "Settings", href: "/admin/settings", icon: Settings },
      { label: "Page Management", href: "/admin/page-management", icon: PanelsTopLeft },
    ],
  },
];
