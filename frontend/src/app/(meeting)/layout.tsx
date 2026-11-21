import MeetingGuard from "@/features/video-rooms/components/meeting-guard";

export const metadata = { title: "VIZU — Video dars" };

export default function MeetingLayout({ children }: { children: React.ReactNode }) {
  return <MeetingGuard>{children}</MeetingGuard>;
}
