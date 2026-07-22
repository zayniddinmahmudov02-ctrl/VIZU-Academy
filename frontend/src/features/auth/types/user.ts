export interface CurrentUser {
  id: string;
  email: string;
  username: string;
  isActive: boolean;
  isVerified: boolean;
  role: string;
}
