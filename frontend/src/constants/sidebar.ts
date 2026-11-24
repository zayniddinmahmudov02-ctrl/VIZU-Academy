import {
  Award,
  BookOpen,
  BookText,
  GraduationCap,
  Info,
  LayoutDashboard,
  Library,
  Settings,
  Tag,
  UserRoundSearch,
  Users,
} from "lucide-react";

import BattleIcon from "@/components/icons/battle-icon";

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
    titleKey: "sidebar.battle",
    href: "/battle",
    icon: BattleIcon,
  },
  {
    titleKey: "sidebar.medien",
    href: "/medien",
    icon: Library,
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
  // "Hilfe Anfragen" (/support) left the menu on 2026-11-24 (owner): My Teacher takes its place. The /support pages and every
  // existing ticket stay reachable by their links (notifications) — nothing was deleted.
  {
    titleKey: "sidebar.myTeacher",
    href: "/my-teacher",
    icon: UserRoundSearch,
  },
  {
    titleKey: "sidebar.settings",
    href: "/settings",
    icon: Settings,
  },
];
