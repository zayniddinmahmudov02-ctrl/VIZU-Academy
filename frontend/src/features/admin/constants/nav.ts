import {
  Award,
  BarChart3,
  BookOpen,
  ClipboardList,
  CreditCard,
  FileCheck,
  FileText,
  FolderOpen,
  Globe,
  Headphones,
  HelpCircle,
  LayoutDashboard,
  Layers3,
  Mic,
  PenLine,
  Settings,
  SpellCheck,
  TrendingUp,
  Users,
  Video,
  type LucideIcon,
} from "lucide-react";

export interface AdminNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export interface AdminNavGroup {
  items: AdminNavItem[];
}

export const ADMIN_NAV_GROUPS: AdminNavGroup[] = [
  {
    items: [
      { label: "Dashboard", href: "/admin", icon: LayoutDashboard },
      { label: "Languages", href: "/admin/languages", icon: Globe },
      { label: "Levels", href: "/admin/levels", icon: BarChart3 },
      { label: "Modules", href: "/admin/modules", icon: Layers3 },
      { label: "Lessons", href: "/admin/lessons", icon: BookOpen },
    ],
  },
  {
    items: [
      { label: "Video Lessons", href: "/admin/videos", icon: Video },
      { label: "Vocabulary", href: "/admin/vocabulary", icon: SpellCheck },
      { label: "Grammar", href: "/admin/grammar", icon: FileText },
      { label: "Reading (Lesen)", href: "/admin/reading", icon: BookOpen },
      { label: "Listening (Hören)", href: "/admin/listening", icon: Headphones },
      { label: "Writing (Schreiben)", href: "/admin/writing", icon: PenLine },
      { label: "Speaking (Sprechen)", href: "/admin/speaking", icon: Mic },
      { label: "Homework", href: "/admin/homework", icon: ClipboardList },
      { label: "Quiz", href: "/admin/quiz", icon: HelpCircle },
      { label: "Media Library", href: "/admin/media", icon: FolderOpen },
    ],
  },
  {
    items: [
      { label: "Mock Exams", href: "/admin/mock-exams", icon: FileCheck },
      { label: "Students", href: "/admin/students", icon: Users },
      { label: "Certificates", href: "/admin/certificates", icon: Award },
      { label: "Payments", href: "/admin/payments", icon: CreditCard },
      { label: "Analytics", href: "/admin/analytics", icon: TrendingUp },
      { label: "Settings", href: "/admin/settings", icon: Settings },
    ],
  },
];
