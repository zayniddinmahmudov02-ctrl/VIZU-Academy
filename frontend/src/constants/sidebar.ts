import {
  Award,
  BookOpen,
  BookText,
  GraduationCap,
  Info,
  LayoutDashboard,
  LifeBuoy,
  Settings,
  Tag,
  Users,
} from "lucide-react";

export const sidebarItems = [
  {
    titleKey: "sidebar.dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    titleKey: "sidebar.courses",
    href: "/kurse",
    icon: BookOpen,
  },
  {
    titleKey: "sidebar.vorbereitung",
    href: "/vorbereitung",
    icon: GraduationCap,
  },
  {
    titleKey: "sidebar.groups",
    href: "/groups",
    icon: Users,
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
    titleKey: "sidebar.support",
    href: "/support",
    icon: LifeBuoy,
  },
  {
    titleKey: "sidebar.settings",
    href: "/settings",
    icon: Settings,
  },
];
