import { redirect } from "next/navigation";

/** VIZU-Pay was renamed to "Angebote" — old links and bookmarks keep working. */
export default function VizuPayRedirect() {
  redirect("/angebote");
}
