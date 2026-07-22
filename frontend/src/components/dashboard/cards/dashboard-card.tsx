import { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string;
  description: string;
  icon: LucideIcon;
}

export default function DashboardCard({
  title,
  value,
  description,
  icon: Icon,
}: Props) {
  return (
    <div
      className="
        group
        rounded-3xl
        border
        border-slate-200
        bg-white
        p-6
        shadow-sm
        transition-all
        duration-300
        hover:-translate-y-1
        hover:shadow-xl
      "
    >
      <div className="flex items-center justify-between">

        <div>

          <p className="text-sm text-slate-500">
            {title}
          </p>

          <h2 className="mt-2 text-3xl font-bold">
            {value}
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            {description}
          </p>

        </div>

        <div
          className="
            flex
            h-16
            w-16
            items-center
            justify-center
            rounded-2xl
            bg-gradient-to-br
            from-blue-700
            to-sky-500
            text-white
          "
        >
          <Icon size={30} />
        </div>

      </div>
    </div>
  );
}