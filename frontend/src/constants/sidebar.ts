import {
  Award,
  BookOpen,
  BookText,
  CreditCard,
  GraduationCap,
  Info,
  LayoutDashboard,
  Settings,
  User,
} from "lucide-react";

export const sidebarItems = [
  {
    titleKey: "sidebar.dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    titleKey: "sidebar.courses",
    href: "/courses",
    icon: BookOpen,
  },
  {
    titleKey: "sidebar.vorbereitung",
    href: "/vorbereitung",
    icon: GraduationCap,
  },
  {
    titleKey: "sidebar.certificates",
    href: "/certificates",
    icon: Award,
  },
  {
    titleKey: "sidebar.dictionary",
    href: "/woerterbuch",
    icon: BookText,
  },
  {
    titleKey: "sidebar.informationen",
    href: "/informationen",
    icon: Info,
  },
  {
    titleKey: "sidebar.vizuPay",
    href: "/vizu-pay",
    icon: CreditCard,
  },
  {
    titleKey: "sidebar.profile",
    href: "/profile",
    icon: User,
  },
  {
    titleKey: "sidebar.settings",
    href: "/settings",
    icon: Settings,
  },
];
