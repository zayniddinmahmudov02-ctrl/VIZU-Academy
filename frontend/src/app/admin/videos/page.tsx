"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import VideoManager from "@/features/admin/components/managers/video-manager";

export default function VideosPage() {
  return (
    <div>
      <AdminPageHeader
        title="Video Lessons"
        description="Videos je Lektion hochladen, ersetzen und veröffentlichen."
      />
      <VideoManager />
    </div>
  );
}
