import {
  Award,
  BookOpen,
  BookText,
  GraduationCap,
  Info,
  LayoutDashboard,
  Settings,
  Tag,
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
    titleKey: "sidebar.angebote",
    href: "/angebote",
    icon: Tag,
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
