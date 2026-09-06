"use client";

import { RotateCw } from "lucide-react";
import Button from "@/components/ui/button";

/** Separated into its own Client Component so the parent page can stay
 * a Server Component (needed for the static `metadata` export) while
 * still getting a real, working retry action. */
export default function OfflineRetryButton() {
  return (
    <Button onClick={() => window.location.reload()} className="mt-2">
      <RotateCw size={16} />
      Erneut versuchen
    </Button>
  );
}
