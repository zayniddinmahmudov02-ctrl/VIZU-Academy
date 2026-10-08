/** Client-side check for "E-mail yoki telefon raqami" — mirrors the backend
 * (backend/app/services/auth/identifier.py), which stays authoritative. */
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidIdentifier(value: string): boolean {
  const text = value.trim();
  if (text.includes("@")) return EMAIL.test(text);
  const compact = text.replace(/[\s\-().]/g, "");
  const digits = compact.replace(/^(\+|00)/, "");
  return /^\d+$/.test(digits) && digits.length >= 9 && digits.length <= 15;
}
