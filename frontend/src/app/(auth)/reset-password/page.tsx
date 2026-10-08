import { redirect } from "next/navigation";

// There is no self-service password reset any more (no e-mail, code or
// token): old reset links land on the "Parolni unutdingizmi?" help page.
export default function ResetPasswordPage() {
  redirect("/forgot-password");
}
