import {
  Award,
  BarChart3,
  Bell,
  BookOpen,
  CreditCard,
  Cpu,
  FolderOpen,
  GraduationCap,
  LayoutDashboard,
  Library,
  MessageSquare,
  ScrollText,
  Settings,
  ShieldCheck,
  Target,
  Ticket,
  Users,
  Video,
  type LucideIcon,
} from "lucide-react";

export interface AdminNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const adminNavItems: AdminNavItem[] = [
  { label: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { label: "Users", href: "/admin/users", icon: Users },
  { label: "Courses", href: "/admin/courses", icon: BookOpen },
  { label: "Lessons", href: "/admin/lessons", icon: GraduationCap },
  { label: "Videos", href: "/admin/videos", icon: Video },
  { label: "Vocabulary", href: "/admin/vocabulary", icon: Library },
  { label: "Preparation", href: "/admin/preparation", icon: Target },
  { label: "Certificates", href: "/admin/certificates", icon: Award },
  { label: "Payments", href: "/admin/payments", icon: CreditCard },
  { label: "Promo Codes", href: "/admin/promo-codes", icon: Ticket },
  { label: "Analytics", href: "/admin/analytics", icon: BarChart3 },
  { label: "Notifications", href: "/admin/notifications", icon: Bell },
  { label: "Media Library", href: "/admin/media", icon: FolderOpen },
  { label: "Feedback", href: "/admin/feedback", icon: MessageSquare },
  { label: "Logs", href: "/admin/logs", icon: ScrollText },
  { label: "Settings", href: "/admin/settings", icon: Settings },
  { label: "System", href: "/admin/system", icon: Cpu },
  { label: "Admins", href: "/admin/admins", icon: ShieldCheck },
];
