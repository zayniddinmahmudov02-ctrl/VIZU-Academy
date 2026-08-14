import { useQuery } from "@tanstack/react-query";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { getDashboard } from "../services/dashboard-service";

export function useDashboard() {
  const { user } = useCurrentUser();

  return useQuery({
    queryKey: ["dashboard-overview", user?.id],
    queryFn: () => getDashboard(user!.id),
    enabled: !!user?.id,
  });
}
