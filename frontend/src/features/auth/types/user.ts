export interface CurrentUser {
  id: string;
  email: string;
  username: string;
  firstName: string | null;
  lastName: string | null;
  phoneNumber: string | null;
  country: string | null;
  profileImage: string | null;
  preferredLanguage: string;
  isActive: boolean;
  isVerified: boolean;
  isBanned: boolean;
  suspendedUntil: string | null;
  role: string;
  createdAt: string;
}
