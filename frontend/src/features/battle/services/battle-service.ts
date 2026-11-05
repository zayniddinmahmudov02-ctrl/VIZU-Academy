import { api } from "@/services/api";

const BASE = "/api/v1/battle";

export type Stage = "A1" | "A2" | "B1" | "B2" | "C1" | "C1+";
export const STAGES: Stage[] = ["A1", "A2", "B1", "B2", "C1", "C1+"];

export interface RankInfo {
  index: number;
  stage: Stage;
  tier: number;
  title: string;
  stage_subtitle: string;
  floor: number;
  next_at: number | null;
  next_title: string | null;
  remaining: number | null;
  progress: number;
}

export interface PlayerCard {
  name: string;
  avatar: string;
  points: number;
  rank: string;
  stage: Stage;
  is_bot: boolean;
}

export interface Attribution {
  title?: string;
  author?: string;
  license?: string;
  license_url?: string;
  source_url?: string;
}

export interface Theme {
  stage: Stage;
  city: string;
  title: string;
  subtitle: string | null;
  desktop_image: string | null;
  mobile_image: string | null;
  accent: string;
  overlay: number;
  attribution: Attribution;
  is_active: boolean;
  published_at: string | null;
}

export interface Stats {
  matches: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  streak: number;
  best_streak: number;
}

export interface Achievement {
  key: string;
  title_de: string;
  title_uz: string;
  unlocked: boolean;
  progress: number;
  goal: number;
}

export interface AvatarOption {
  key: string;
  title: string;
  unlocked: boolean;
  unlock_rank: string;
  selected: boolean;
}

export interface RecentMatch {
  id: string;
  mode: MatchMode;
  stage: Stage;
  result: "win" | "loss" | "draw";
  finish_reason: string | null;
  my_score: number;
  opponent_score: number;
  points_delta: number;
  opponent: string;
  finished_at: string | null;
}

export interface LeaderRow extends PlayerCard {
  position: number;
  wins: number;
  matches: number;
  me: boolean;
}

export interface Leaderboard {
  items: LeaderRow[];
  total: number;
  page: number;
  page_size: number;
  me: PlayerCard & { position: number };
}

export interface BattleHome {
  player: PlayerCard;
  rank: RankInfo;
  stats: Stats;
  achievements: Achievement[];
  avatars: AvatarOption[];
  recent: RecentMatch[];
  leaderboard: { items: LeaderRow[]; me: PlayerCard & { position: number } };
  ladder: { index: number; title: string; stage: Stage; at: number }[];
  theme: Theme;
  themes: Theme[];
  open_match_id: string | null;
  playable: boolean;
  pool: number;
  min_pool: number;
  rules: { rounds: number; round_s: number; base: number; speed_bonus: number; win: number; draw: number; loss: number };
}

export type MatchMode = "ranked" | "private" | "bot";
export type MatchStatus = "waiting" | "active" | "finished" | "cancelled";

export interface MatchPlayer extends PlayerCard {
  score: number;
}

export interface RoundView {
  no: number;
  total: number;
  phase: "question" | "reveal";
  started_at: string;
  deadline: string;
  reveal_ends_at: string | null;
  image_url: string;
  category: { de: string; uz: string } | null;
  options: string[];
  my_answer: { choice: number | null; correct: boolean; score: number; time_ms: number } | null;
  opponent_answered: boolean;
  correct: number | null;
  translation: string | null;
  opponent_choice: number | null;
}

export interface MatchResult {
  outcome: "win" | "loss" | "draw";
  reason: "normal" | "forfeit" | "afk" | null;
  ranked: boolean;
  points_delta: number;
  points_after: number;
  rank_before: RankInfo;
  rank_after: RankInfo;
  rank_up: boolean;
  stage_up: boolean;
}

export interface MatchState {
  id: string;
  mode: MatchMode;
  status: MatchStatus;
  stage: Stage;
  server_time: string;
  room_code: string | null;
  waiting_since: string | null;
  countdown_ends_at: string | null;
  rounds: number;
  me: MatchPlayer;
  opponent: MatchPlayer | null;
  round: RoundView | null;
  history: { round: number; me: boolean | null; opponent: boolean | null }[];
  result: MatchResult | null;
  timing: { round_s: number; reveal_s: number; afk_s: number };
}

export const getBattleHome = async () => (await api.get<BattleHome>(`${BASE}/home`)).data;

export const getLeaderboard = async (stage: Stage | "", page = 1) =>
  (await api.get<Leaderboard>(`${BASE}/leaderboard`, { params: { ...(stage ? { stage } : {}), page } })).data;

export const setAvatar = async (avatar: string) =>
  (await api.put<{ avatar: string; avatars: AvatarOption[] }>(`${BASE}/profile/avatar`, { avatar })).data;

export const joinQueue = async () => (await api.post<MatchState>(`${BASE}/queue`)).data;
export const startPractice = async () => (await api.post<MatchState>(`${BASE}/practice`)).data;
export const createRoom = async () => (await api.post<MatchState>(`${BASE}/rooms`)).data;
export const joinRoom = async (code: string) => (await api.post<MatchState>(`${BASE}/rooms/join`, { code })).data;

export const getMatch = async (id: string, signal?: AbortSignal) =>
  (await api.get<MatchState>(`${BASE}/matches/${encodeURIComponent(id)}`, { signal })).data;

export const sendAnswer = async (id: string, round: number, choice: number) =>
  (await api.post<MatchState>(`${BASE}/matches/${encodeURIComponent(id)}/answer`, { round, choice })).data;

export const leaveMatch = async (id: string) => (await api.post<MatchState>(`${BASE}/matches/${encodeURIComponent(id)}/leave`)).data;

export function battleError(err: unknown): string {
  const data = (err as { response?: { data?: { message?: unknown } } })?.response?.data;
  return typeof data?.message === "string" ? data.message.split(":")[0] : "UNKNOWN";
}
