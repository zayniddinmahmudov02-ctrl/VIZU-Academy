import type { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  description: string;
  icon: LucideIcon;
}

export default function LessonHeader({ title, description, icon: Icon }: Props) {
  return (
    <div className="mb-6 flex items-start gap-4 sm:mb-8 sm:gap-5">
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-accent-blue to-purple-600 text-white shadow-md sm:h-14 sm:w-14">
        <Icon size={24} />
      </div>

      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">{title}</h2>
        <p className="mt-1.5 text-sm text-text-secondary sm:text-base">{description}</p>
      </div>
    </div>
  );
}
