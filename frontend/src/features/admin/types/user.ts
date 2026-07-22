export interface UserTag {
  id: string;
  label: string;
}

export interface AdminUserListItem {
  id: string;
  email: string;
  username: string;
  role: string;
  isActive: boolean;
  isVerified: boolean;
  isBanned: boolean;
  isSuspended: boolean;
  isPremium: boolean;
  premiumUntil: string | null;
  lastLogin: string | null;
  createdAt: string;
  tags: UserTag[];
}

export interface AdminUserListResponse {
  items: AdminUserListItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface AdminUserDetail extends Omit<AdminUserListItem, "isSuspended"> {
  banReason: string | null;
  bannedAt: string | null;
  isSuspended: boolean;
  suspendedUntil: string | null;
  suspendReason: string | null;
  enrollmentsCount: number;
  certificatesCount: number;
  paymentsTotal: number;
}

export interface UserProgressLesson {
  lessonId: string;
  lessonTitle: string;
  courseTitle: string;
  totalScore: number;
  lessonCompleted: boolean;
  videoCompleted: boolean;
  grammarCompleted: boolean;
  readingCompleted: boolean;
  listeningCompleted: boolean;
  writingCompleted: boolean;
  speakingCompleted: boolean;
  quizCompleted: boolean;
}

export interface UserProgress {
  totalLessonsStarted: number;
  totalLessonsCompleted: number;
  totalExperience: number;
  totalStudyMinutes: number;
  longestStreakDays: number;
  lessons: UserProgressLesson[];
}

export interface LoginHistoryItem {
  id: string;
  ipAddress: string | null;
  device: string;
  os: string;
  browser: string;
  success: boolean;
  createdAt: string;
}

export interface LoginHistoryResponse {
  items: LoginHistoryItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface DeviceHistoryItem {
  device: string;
  os: string;
  browser: string;
  ipAddress: string | null;
  firstSeen: string;
  lastSeen: string;
  loginCount: number;
}

export interface ActivityTimelineItem {
  type: string;
  title: string;
  timestamp: string;
}

export interface PaymentHistoryItem {
  id: string;
  courseTitle: string;
  amount: number;
  currency: string;
  provider: string;
  status: string;
  transactionId: string | null;
  createdAt: string;
}

export interface SubscriptionInfo {
  isPremium: boolean;
  premiumUntil: string | null;
  isTrial: boolean;
  totalPaid: number;
  paymentsCount: number;
}

export interface AuditLogItem {
  id: string;
  actorEmail: string | null;
  action: string;
  details: string | null;
  ipAddress: string | null;
  createdAt: string;
}

export interface AuditLogResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface UserListQuery {
  page: number;
  pageSize: number;
  search?: string;
  role?: string;
  status?: string;
  tag?: string;
  sortBy?: string;
  sortDir?: "asc" | "desc";
}

export interface ImpersonateResult {
  accessToken: string;
  tokenType: string;
  user: AdminUserListItem;
}
