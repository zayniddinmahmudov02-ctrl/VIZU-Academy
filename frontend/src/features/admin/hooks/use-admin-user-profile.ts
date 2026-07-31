"use client";

import { useCallback, useState } from "react";

import { useAsyncResource } from "./use-async-resource";
import * as usersService from "../services/users-service";

export function useAdminUserProfile(userId: string) {
  const [loginHistoryPage, setLoginHistoryPage] = useState(1);
  const [auditLogPage, setAuditLogPage] = useState(1);
  const [actionPending, setActionPending] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const detail = useAsyncResource(() => usersService.getUserDetail(userId), [userId]);
  const progress = useAsyncResource(() => usersService.getUserProgress(userId), [userId]);
  const subscription = useAsyncResource(() => usersService.getSubscription(userId), [userId]);
  const loginHistory = useAsyncResource(
    () => usersService.getLoginHistory(userId, loginHistoryPage),
    [userId, loginHistoryPage],
  );
  const deviceHistory = useAsyncResource(() => usersService.getDeviceHistory(userId), [userId]);
  const activity = useAsyncResource(() => usersService.getActivityTimeline(userId), [userId]);
  const payments = useAsyncResource(() => usersService.getPaymentHistory(userId), [userId]);
  const auditLog = useAsyncResource(
    () => usersService.getAuditLog(userId, auditLogPage),
    [userId, auditLogPage],
  );

  const refetchAll = useCallback(() => {
    detail.refetch();
    subscription.refetch();
    activity.refetch();
    auditLog.refetch();
    payments.refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runAction = useCallback(
    async <T,>(action: () => Promise<T>): Promise<T | null> => {
      setActionPending(true);
      setActionError(null);
      try {
        const result = await action();
        refetchAll();
        return result;
      } catch (err) {
        console.warn("Admin user action failed:", err);
        setActionError("Action failed. Please try again.");
        return null;
      } finally {
        setActionPending(false);
      }
    },
    [refetchAll],
  );

  return {
    detail,
    progress,
    subscription,
    loginHistory,
    loginHistoryPage,
    setLoginHistoryPage,
    deviceHistory,
    activity,
    payments,
    auditLog,
    auditLogPage,
    setAuditLogPage,
    actionPending,
    actionError,

    grantPremium: (days: number) => runAction(() => usersService.grantPremium(userId, days)),
    extendSubscription: (days: number) => runAction(() => usersService.extendSubscription(userId, days)),
    ban: (reason: string) => runAction(() => usersService.banUser(userId, reason)),
    unban: () => runAction(() => usersService.unbanUser(userId)),
    updateRole: (role: string) => runAction(() => usersService.updateUserRole(userId, role)),
    suspend: (days: number, reason: string) => runAction(() => usersService.suspendUser(userId, days, reason)),
    unsuspend: () => runAction(() => usersService.unsuspendUser(userId)),
    resetPassword: () => runAction(() => usersService.resetPassword(userId)),
    addTag: (label: string) => runAction(() => usersService.addTag(userId, label)),
    removeTag: (tagId: string) => runAction(() => usersService.removeTag(userId, tagId)),
    impersonate: () => runAction(() => usersService.impersonateUser(userId)),
  };
}
