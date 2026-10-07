import { redirect } from "next/navigation";

// Password reset is code-based now (Passwort vergessen -> 6-digit code);
// old e-mailed reset links land on the new flow.
export default function ResetPasswordPage() {
  redirect("/forgot-password");
}
