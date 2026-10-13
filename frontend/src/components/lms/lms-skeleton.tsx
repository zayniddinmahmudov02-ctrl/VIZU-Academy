import { cn } from "@/lib/utils";

function Bar({ className }: { className?: string }) {
  return <div className={cn("lms-skeleton rounded-lg", className)} />;
}

/** Loading placeholder of the LMS pages — the shape of what is coming
 * instead of a spinner. */
export default function LmsSkeleton({ variant = "lesson" }: { variant?: "lesson" | "grid" }) {
  return (
    <div className="space-y-6" data-testid="lms-skeleton" aria-busy="true" aria-live="polite">
      <div className="space-y-3 rounded-card bg-surface-card p-5 ring-1 ring-surface-border sm:p-6">
        <Bar className="h-3 w-40" />
        <Bar className="h-7 w-2/3" />
        <Bar className="h-3 w-1/2" />
        {variant === "lesson" && <Bar className="mt-4 h-1.5 w-full" />}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="space-y-3 rounded-card bg-surface-card p-4 ring-1 ring-surface-border">
            <div className="flex items-center gap-3">
              <Bar className="h-10 w-10 rounded-xl" />
              <div className="flex-1 space-y-2">
                <Bar className="h-3 w-1/3" />
                <Bar className="h-4 w-2/3" />
              </div>
            </div>
            <Bar className="h-9 w-full rounded-xl" />
          </div>
        ))}
      </div>
    </div>
  );
}
