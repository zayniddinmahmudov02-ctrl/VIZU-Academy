import { api } from "@/services/api";

/** Group video lessons. Every rule is enforced by the backend (services/video_rooms); the UI only mirrors it. */

const GROUPS = "/api/v1/groups";
const ROOMS = "/api/v1/video-rooms";

export type RoomStatus = "scheduled" | "live" | "ended" | "cancelled";
export type ConnectionStatus = "joining" | "connected" | "reconnecting" | "disconnected" | "left" | "removed";

export interface VideoRoom {
  id: string;
  group_id: string;
  title: string;
  description: string | null;
  status: RoomStatus;
  scheduled_at: string | null;
  started_at: string | null;
  ended_at: string | null;
  end_reason: string | null;
  max_participants: number;
  chat_enabled: boolean;
  students_can_share_screen: boolean;
  students_mic_allowed: boolean;
  created_by: { id: string; name: string } | null;
  online_count: number;
  created_at: string;
}

export interface RoomPermissions {
  role: "host" | "student";
  camera: boolean;
  microphone: boolean;
  screen_share: boolean;
  chat: boolean;
  moderate: boolean;
}

export interface GroupRooms { live: VideoRoom | null; upcoming: VideoRoom[]; past: VideoRoom[]; is_manager: boolean; configured: boolean }
export interface ActiveRoom { room: VideoRoom | null; is_manager: boolean; configured: boolean }
export interface GroupRef { id: string; name: string; level: string }

export interface RoomDetail {
  room: VideoRoom;
  group: GroupRef;
  viewer: { is_manager: boolean; permissions: RoomPermissions; connection_status: ConnectionStatus | null; blocked: boolean; hand_raised_at: string | null };
  configured: boolean;
}

export interface JoinInfo { server_url: string; token: string; expires_in: number; identity: string; room: VideoRoom; group: GroupRef; permissions: RoomPermissions }

export interface ParticipantRow {
  user_id: string;
  name: string;
  role: "host" | "student";
  connection_status: ConnectionStatus;
  joined_at: string | null;
  hand_raised_at: string | null;
  can_speak: boolean;
  can_share_screen: boolean;
  can_chat: boolean;
  mic_on: boolean;
  camera_on: boolean;
  screen_sharing: boolean;
  left_at?: string | null;
  join_count?: number;
  blocked?: boolean;
  removed_at?: string | null;
}

export interface ParticipantsOut { items: ParticipantRow[]; online_count: number; livekit: "available" | "unavailable" | "unconfigured"; absent?: { user_id: string; name: string }[] }

export interface RoomCreate {
  title: string;
  description?: string | null;
  scheduled_at?: string | null;
  start_now?: boolean;
  chat_enabled?: boolean;
  students_can_share_screen?: boolean;
}

export interface AdminRoom extends VideoRoom {
  group: { id: string; name: string; level: string | null; teacher: string };
  server_participants: number | null;
  server_room_active: boolean | null;
}

export interface AdminOverview {
  livekit_status: "available" | "unavailable" | "unconfigured";
  live: AdminRoom[];
  scheduled: AdminRoom[];
  recent: AdminRoom[];
  totals: { live: number; scheduled: number; online: number };
  limits: { max_participants: number; token_ttl_seconds: number };
}

// rooms of a group
export const listRooms = (groupId: string) => api.get<GroupRooms>(`${GROUPS}/${groupId}/video-rooms`).then((r) => r.data);
export const activeRoom = (groupId: string) => api.get<ActiveRoom>(`${GROUPS}/${groupId}/video-rooms/active`).then((r) => r.data);
export const createRoom = (groupId: string, body: RoomCreate) => api.post<VideoRoom>(`${GROUPS}/${groupId}/video-rooms`, body).then((r) => r.data);

// one room
export const getRoom = (roomId: string) => api.get<RoomDetail>(`${ROOMS}/${roomId}`).then((r) => r.data);
export const startRoom = (roomId: string) => api.post<VideoRoom>(`${ROOMS}/${roomId}/start`).then((r) => r.data);
export const cancelRoom = (roomId: string) => api.post<VideoRoom>(`${ROOMS}/${roomId}/cancel`).then((r) => r.data);
export const endRoom = (roomId: string) => api.post<{ room: VideoRoom; livekit_closed: boolean }>(`${ROOMS}/${roomId}/end`).then((r) => r.data);
export const joinRoom = (roomId: string) => api.post<JoinInfo>(`${ROOMS}/${roomId}/join`).then((r) => r.data);
export const leaveRoom = (roomId: string) => api.post<{ ok: boolean }>(`${ROOMS}/${roomId}/leave`).then((r) => r.data);
export const getParticipants = (roomId: string) => api.get<ParticipantsOut>(`${ROOMS}/${roomId}/participants`).then((r) => r.data);
export const reportConnection = (roomId: string, state: "connected" | "reconnecting" | "disconnected" | "failed", quality?: string) =>
  api.post(`${ROOMS}/${roomId}/connection`, quality ? { state, quality } : { state }).then((r) => r.data);
export const raiseHand = (roomId: string, raised: boolean, userId?: string) =>
  api.post<{ user_id: string; hand_raised_at: string | null }>(`${ROOMS}/${roomId}/raise-hand`, userId ? { raised, user_id: userId } : { raised }).then((r) => r.data);

// teacher moderation (the backend checks that the caller manages this room's group)
export const muteParticipant = (roomId: string, userId: string) => api.post(`${ROOMS}/${roomId}/mute-participant`, { user_id: userId }).then((r) => r.data);
export const muteAll = (roomId: string, lock = false) => api.post(`${ROOMS}/${roomId}/mute-all`, { lock }).then((r) => r.data);
const permission = (what: "mic" | "screen-share" | "chat") => (roomId: string, allowed: boolean, userId?: string) =>
  api.post(`${ROOMS}/${roomId}/${what}-permission`, userId ? { allowed, user_id: userId } : { allowed }).then((r) => r.data);
export const micPermission = permission("mic");
export const screenSharePermission = permission("screen-share");
export const chatPermission = permission("chat");
export const removeParticipant = (roomId: string, userId: string, block = false) =>
  api.post(`${ROOMS}/${roomId}/remove-participant`, { user_id: userId, block }).then((r) => r.data);

// admin monitoring (SUPER_ADMIN)
export const adminOverview = () => api.get<AdminOverview>("/api/v1/admin/video-rooms").then((r) => r.data);
export const adminEndRoom = (roomId: string) => api.post(`/api/v1/admin/video-rooms/${roomId}/end`).then((r) => r.data);
