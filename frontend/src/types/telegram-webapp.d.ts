// Minimal ambient typing for the Telegram Mini App SDK
// (https://telegram.org/js/telegram-web-app.js), loaded via a plain
// <script> tag (see app/layout.tsx) — not an npm package, so there's no
// @types/* package to install. Only the surface actually used by
// lib/telegram/webapp.ts is typed here; extend as real usage grows
// rather than transcribing the whole upstream SDK up front.

interface TelegramWebAppUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
  photo_url?: string;
}

interface TelegramWebAppInitDataUnsafe {
  query_id?: string;
  user?: TelegramWebAppUser;
  auth_date?: number;
  hash?: string;
  start_param?: string;
}

interface TelegramWebAppThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

interface TelegramWebApp {
  /** Signed, tamper-evident — this is what a future backend endpoint
   * must verify (see backend/app/core/security/telegram.py); never
   * treat initDataUnsafe below as authenticated. */
  initData: string;
  /** Convenience-parsed, NOT verified — UI-only (e.g. showing a name
   * optimistically before the backend confirms it). */
  initDataUnsafe: TelegramWebAppInitDataUnsafe;
  version: string;
  platform: string;
  colorScheme: "light" | "dark";
  themeParams: TelegramWebAppThemeParams;
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  headerColor: string;
  backgroundColor: string;
  isClosingConfirmationEnabled: boolean;
  ready: () => void;
  expand: () => void;
  close: () => void;
  onEvent: (eventType: string, callback: () => void) => void;
  offEvent: (eventType: string, callback: () => void) => void;
}

interface Window {
  Telegram?: {
    WebApp: TelegramWebApp;
  };
}
