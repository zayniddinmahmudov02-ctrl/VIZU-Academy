import {
  Award,
  BookOpen,
  ClipboardList,
  CreditCard,
  Crown,
  FlaskConical,
  GraduationCap,
  Globe,
  LayoutDashboard,
  School,
  Settings,
  ShieldCheck,
  TrendingUp,
  Users,
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

// CMS reorganization: the sidebar now exposes exactly the 12 top-level
// sections requested. Everything that used to be a standalone sidebar item
// (Modules, Lessons, Video Lessons, Vocabulary, Grammar, Reading,
// Listening, Writing, Speaking, Quiz, Media Library) still exists and is
// fully functional at its original route — those routes are just no
// longer linked directly from the sidebar. They're reached instead through
// Courses -> Level -> Lesson, which manages the same underlying data.
export const ADMIN_NAV_GROUPS: AdminNavGroup[] = [
  {
    items: [
      { label: "Dashboard", href: "/admin", icon: LayoutDashboard },
      { label: "Languages", href: "/admin/languages", icon: Globe },
      { label: "Courses", href: "/admin/courses", icon: GraduationCap },
      { label: "Vorbereitung", href: "/admin/mock-exams", icon: ShieldCheck },
      { label: "VIZU-MOCK", href: "/admin/vizu-mock", icon: FlaskConical },
      { label: "Users", href: "/admin/users", icon: Users },
      { label: "Lehrer-Zuweisungen", href: "/admin/teacher-assignments", icon: School },
      { label: "Premium-Users", href: "/admin/premium-users", icon: Crown },
      { label: "Certificate", href: "/admin/certificates", icon: Award },
      { label: "Bücher", href: "/admin/books", icon: BookOpen },
      { label: "Payments", href: "/admin/payments", icon: CreditCard },
      { label: "Analytics", href: "/admin/analytics", icon: TrendingUp },
      { label: "Homeworks", href: "/admin/homeworks", icon: ClipboardList },
      { label: "Settings", href: "/admin/settings", icon: Settings },
    ],
  },
];
