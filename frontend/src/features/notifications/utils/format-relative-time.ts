export function formatRelativeTime(
  dateStr: string,
  t: (key: string, vars?: Record<string, string | number>) => string,
): string {
  const date = new Date(dateStr);
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return t("notifications.timeJustNow");
  if (diffMin < 60) return t("notifications.timeMinutesAgo", { count: diffMin });

  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return t("notifications.timeHoursAgo", { count: diffHours });

  const diffDays = Math.floor(diffHours / 24);
  return t("notifications.timeDaysAgo", { count: diffDays });
}
