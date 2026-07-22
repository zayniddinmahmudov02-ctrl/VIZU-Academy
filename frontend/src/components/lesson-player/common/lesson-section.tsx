"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

import { cardEntrance } from "@/lib/motion";
import LessonHeader from "./lesson-header";

interface Props {
  title: string;
  description: string;
  icon: LucideIcon;
  children: ReactNode;
}

export default function LessonSection({
  title,
  description,
  icon,
  children,
}: Props) {
  return (
    <motion.section
      variants={cardEntrance}
      initial="hidden"
      animate="show"
      className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-8"
    >
      <LessonHeader title={title} description={description} icon={icon} />

      {children}
    </motion.section>
  );
}
