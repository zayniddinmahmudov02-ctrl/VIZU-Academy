import {
  Award,
  BookOpen,
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
      // "Homeworks" (the Schreiben/Sprechen submission review queue,
      // /admin/homeworks) is deliberately no longer linked here — that
      // operational review workflow now lives in the Teacher Panel
      // (Schreiben/Sprechen, scoped per-teacher via TeacherAssignment).
      // The route/page/data are untouched (nothing deleted, no admin
      // access removed), just unlinked from the sidebar, same convention
      // as the CMS reorganization note above. The unrelated Homework
      // *task* CRUD (/admin/homework, singular — title/description/
      // max_score content management) was never linked here either and
      // stays reachable via Courses -> Level -> Lesson, unaffected.
      { label: "Settings", href: "/admin/settings", icon: Settings },
    ],
  },
];
