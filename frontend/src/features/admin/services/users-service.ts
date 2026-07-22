import { api } from "@/services/api";

import type {
  AdminUserDetail,
  AdminUserListResponse,
  AuditLogResponse,
  DeviceHistoryItem,
  ActivityTimelineItem,
  ImpersonateResult,
  LoginHistoryResponse,
  PaymentHistoryItem,
  SubscriptionInfo,
  UserListQuery,
  UserProgress,
  UserTag,
} from "../types/user";

function mapTag(raw: { id: string; label: string }): UserTag {
  return { id: raw.id, label: raw.label };
}

function mapListItem(raw: any) {
  return {
    id: raw.id,
    email: raw.email,
    username: raw.username,
    role: raw.role,
    isActive: raw.is_active,
    isVerified: raw.is_verified,
    isBanned: raw.is_banned,
    isSuspended: raw.is_suspended,
    isPremium: raw.is_premium,
    premiumUntil: raw.premium_until,
    lastLogin: raw.last_login,
    createdAt: raw.created_at,
    tags: (raw.tags ?? []).map(mapTag),
  };
}

function mapDetail(raw: any): AdminUserDetail {
  return {
    ...mapListItem(raw),
    banReason: raw.ban_reason,
    bannedAt: raw.banned_at,
    suspendedUntil: raw.suspended_until,
    suspendReason: raw.suspend_reason,
    enrollmentsCount: raw.enrollments_count,
    certificatesCount: raw.certificates_count,
    paymentsTotal: raw.payments_total,
  };
}

function buildParams(query: Partial<UserListQuery>) {
  const params: Record<string, string | number> = {};
  if (query.page) params.page = query.page;
  if (query.pageSize) params.page_size = query.pageSize;
  if (query.search) params.search = query.search;
  if (query.role) params.role = query.role;
  if (query.status) params.status = query.status;
  if (query.tag) params.tag = query.tag;
  if (query.sortBy) params.sort_by = query.sortBy;
  if (query.sortDir) params.sort_dir = query.sortDir;
  return params;
}

export async function listUsers(query: UserListQuery): Promise<AdminUserListResponse> {
  const response = await api.get("/admin/users", { params: buildParams(query) });
  const data = response.data;
  return {
    items: data.items.map(mapListItem),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    totalPages: data.total_pages,
  };
}

export async function getUserDetail(userId: string): Promise<AdminUserDetail> {
  const response = await api.get(`/admin/users/${userId}`);
  return mapDetail(response.data);
}

export async function getUserProgress(userId: string): Promise<UserProgress> {
  const response = await api.get(`/admin/users/${userId}/progress`);
  const data = response.data;
  return {
    totalLessonsStarted: data.total_lessons_started,
    totalLessonsCompleted: data.total_lessons_completed,
    totalExperience: data.total_experience,
    totalStudyMinutes: data.total_study_minutes,
    longestStreakDays: data.longest_streak_days,
    lessons: data.lessons.map((l: any) => ({
      lessonId: l.lesson_id,
      lessonTitle: l.lesson_title,
      courseTitle: l.course_title,
      totalScore: l.total_score,
      lessonCompleted: l.lesson_completed,
      videoCompleted: l.video_completed,
      grammarCompleted: l.grammar_completed,
      readingCompleted: l.reading_completed,
      listeningCompleted: l.listening_completed,
      writingCompleted: l.writing_completed,
      speakingCompleted: l.speaking_completed,
      quizCompleted: l.quiz_completed,
    })),
  };
}

export async function getLoginHistory(userId: string, page = 1, pageSize = 20): Promise<LoginHistoryResponse> {
  const response = await api.get(`/admin/users/${userId}/login-history`, { params: { page, page_size: pageSize } });
  const data = response.data;
  return {
    items: data.items.map((i: any) => ({
      id: i.id,
      ipAddress: i.ip_address,
      device: i.device,
      os: i.os,
      browser: i.browser,
      success: i.success,
      createdAt: i.created_at,
    })),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    totalPages: data.total_pages,
  };
}

export async function getDeviceHistory(userId: string): Promise<DeviceHistoryItem[]> {
  const response = await api.get(`/admin/users/${userId}/device-history`);
  return response.data.map((d: any) => ({
    device: d.device,
    os: d.os,
    browser: d.browser,
    ipAddress: d.ip_address,
    firstSeen: d.first_seen,
    lastSeen: d.last_seen,
    loginCount: d.login_count,
  }));
}

export async function getActivityTimeline(userId: string): Promise<ActivityTimelineItem[]> {
  const response = await api.get(`/admin/users/${userId}/activity`);
  return response.data;
}

export async function getPaymentHistory(userId: string): Promise<PaymentHistoryItem[]> {
  const response = await api.get(`/admin/users/${userId}/payments`);
  return response.data.map((p: any) => ({
    id: p.id,
    courseTitle: p.course_title,
    amount: p.amount,
    currency: p.currency,
    provider: p.provider,
    status: p.status,
    transactionId: p.transaction_id,
    createdAt: p.created_at,
  }));
}

export async function getSubscription(userId: string): Promise<SubscriptionInfo> {
  const response = await api.get(`/admin/users/${userId}/subscription`);
  const data = response.data;
  return {
    isPremium: data.is_premium,
    premiumUntil: data.premium_until,
    isTrial: data.is_trial,
    totalPaid: data.total_paid,
    paymentsCount: data.payments_count,
  };
}

export async function grantPremium(userId: string, days: number): Promise<AdminUserDetail> {
  const response = await api.post(`/admin/users/${userId}/grant-premium`, { days });
  return mapDetail(response.data);
}

export async function extendSubscription(userId: string, days: number): Promise<AdminUserDetail> {
  const response = await api.post(`/admin/users/${userId}/extend-subscription`, { days });
  return mapDetail(response.data);
}

export async function banUser(userId: string, reason: string): Promise<AdminUserDetail> {
  const response = await api.post(`/admin/users/${userId}/ban`, { reason });
  return mapDetail(response.data);
}

export async function unbanUser(userId: string): Promise<AdminUserDetail> {
  const response = await api.post(`/admin/users/${userId}/unban`);
  return mapDetail(response.data);
}

export async function suspendUser(userId: string, days: number, reason: string): Promise<AdminUserDetail> {
  const response = await api.post(`/admin/users/${userId}/suspend`, { days, reason });
  return mapDetail(response.data);
}

export async function unsuspendUser(userId: string): Promise<AdminUserDetail> {
  const response = await api.post(`/admin/users/${userId}/unsuspend`);
  return mapDetail(response.data);
}

export async function resetPassword(userId: string): Promise<string> {
  const response = await api.post(`/admin/users/${userId}/reset-password`);
  return response.data.temporary_password;
}

export async function addTag(userId: string, label: string): Promise<UserTag[]> {
  const response = await api.post(`/admin/users/${userId}/tags`, { label });
  return response.data.map(mapTag);
}

export async function removeTag(userId: string, tagId: string): Promise<UserTag[]> {
  const response = await api.delete(`/admin/users/${userId}/tags/${tagId}`);
  return response.data.map(mapTag);
}

export async function impersonateUser(userId: string): Promise<ImpersonateResult> {
  const response = await api.post(`/admin/users/${userId}/impersonate`);
  const data = response.data;
  return {
    accessToken: data.access_token,
    tokenType: data.token_type,
    user: mapListItem(data.user),
  };
}

export async function getAuditLog(userId: string, page = 1, pageSize = 20): Promise<AuditLogResponse> {
  const response = await api.get(`/admin/users/${userId}/audit-log`, { params: { page, page_size: pageSize } });
  const data = response.data;
  return {
    items: data.items.map((a: any) => ({
      id: a.id,
      actorEmail: a.actor_email,
      action: a.action,
      details: a.details,
      ipAddress: a.ip_address,
      createdAt: a.created_at,
    })),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    totalPages: data.total_pages,
  };
}

async function downloadBlob(url: string, params: Record<string, string | number>, filename: string) {
  const response = await api.get(url, { params, responseType: "blob" });
  const blobUrl = window.URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(blobUrl);
}

export async function exportUsersCsv(query: Partial<UserListQuery>): Promise<void> {
  await downloadBlob("/admin/users/export.csv", buildParams(query), "users_export.csv");
}

export async function exportUsersXlsx(query: Partial<UserListQuery>): Promise<void> {
  await downloadBlob("/admin/users/export.xlsx", buildParams(query), "users_export.xlsx");
}
