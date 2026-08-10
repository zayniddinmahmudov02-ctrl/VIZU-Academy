import type { CurrentUser } from "@/features/auth/types/user";

export type AccountStatus = "active" | "banned" | "suspended" | "inactive";

export function getAccountStatus(user: CurrentUser): AccountStatus {
  if (user.isBanned) return "banned";
  if (user.suspendedUntil && new Date(user.suspendedUntil).getTime() > Date.now()) {
    return "suspended";
  }
  if (!user.isActive) return "inactive";
  return "active";
}
