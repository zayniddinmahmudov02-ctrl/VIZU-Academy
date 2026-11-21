"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";

// client only: LiveKit, devices and the per-browser device choice need the browser (no server prerender)
const VideoRoomPage = dynamic(() => import("@/features/video-rooms/components/video-room-page"), { ssr: false });

export default function VideoRoomRoute() {
  const { roomId } = useParams<{ roomId: string }>();
  return <VideoRoomPage roomId={roomId} />;
}
