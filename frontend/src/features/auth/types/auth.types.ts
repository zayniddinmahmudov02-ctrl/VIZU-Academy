/** `identifier` = e-mail address OR phone number (the login). */
export interface LoginRequest {
  identifier: string;
  password: string;
}

export interface RegisterRequest {
  full_name: string;
  identifier: string;
  password: string;
  password_confirm: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  login_phone?: string | null;
}

export interface VerifyAdminPasswordRequest {
  password: string;
}

export interface JwtPayload {
  sub: string;
  email: string;
  role: string;
  iat: number;
  exp: number;
}
