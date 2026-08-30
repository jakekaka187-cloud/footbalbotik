export type Slot = 'GK' | 'DEF' | 'MID1' | 'MID2' | 'FWD'

export interface Player {
  id: number
  name: string
  position: string
  nationality: string
  club: string
  difficulty: number
  rating: number
}

export interface RosterEntry {
  slot: Slot
  player: Player
}

export interface User {
  telegram_id: number
  username: string | null
  first_name: string
  total_score: number
  season_score: number
  games_played: number
  referral_count: number
}

export interface AuthResponse {
  user: User
  start_param: string | null
  subscribed: boolean
  channel_username: string
}

export interface CreateSoloResponse {
  session_id: string
  mode: 'solo'
  status: 'active'
  slots: Slot[]
  current_slot_index: number
}

export interface CreatePvpResponse {
  session_id: string
  mode: 'pvp'
  status: 'waiting'
  room_code: string
  invite_link: string
  expires_at: string
}

export interface ParticipantView {
  telegram_id: number
  current_slot_index: number
  status: 'drafting' | 'done'
  pending_candidate: { slot: Slot; player: Player } | null
  roster: RosterEntry[]
  first_name?: string | null
}

export interface SessionState {
  session_id: string
  mode: 'solo' | 'pvp'
  status: 'waiting' | 'active' | 'finished' | 'expired'
  slots: Slot[]
  me: ParticipantView | null
  opponent: ParticipantView | null
}

export interface RevealResponse {
  slot: Slot
  player: Player
  draw_index: number
}

export interface DecideResponse {
  slot: Slot
  committed_player: Player
  skipped_player?: Player
  alt_player?: Player
  current_slot_index: number
  status: 'drafting' | 'done'
  team_rating: number | null
}

export interface ResultParticipant {
  telegram_id: number
  roster: RosterEntry[]
  team_rating: number
  team_ovr_avg: number
}

export interface ResultResponse {
  session_id: string
  mode: 'solo' | 'pvp'
  finished_at: string
  participants: ResultParticipant[]
}

export interface LeaderboardRow {
  telegram_id: number
  username: string | null
  first_name: string
  score: number
  drafts_completed: number
}

export interface LeaderboardResponse {
  scope: string
  rows: LeaderboardRow[]
  competition_end_date: string
  competition_min_drafts: number
}

export interface ApiErrorBody {
  error: string
}
