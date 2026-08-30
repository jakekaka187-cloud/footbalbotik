import { getDevUserId, getInitData, isInsideTelegram } from './telegram'
import type {
  ApiErrorBody, AuthResponse, CreatePvpResponse, CreateSoloResponse,
  DecideResponse, LeaderboardResponse, ResultResponse, RevealResponse, SessionState,
} from './types'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function authHeaders(): Record<string, string> {
  if (isInsideTelegram) {
    return { Authorization: `tma ${getInitData()}` }
  }
  // Local dev fallback — only works against a backend started with DEV_MODE=1.
  return { 'X-Dev-User-Id': getDevUserId() }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    const body = (await res.json().catch(() => ({ error: res.statusText }))) as ApiErrorBody
    throw new ApiError(body.error ?? 'Request failed', res.status)
  }
  return (await res.json()) as T
}

export const api = {
  auth: () => request<AuthResponse>('/auth', { method: 'POST', body: '{}' }),
  createSolo: () => request<CreateSoloResponse>('/draft/solo', { method: 'POST', body: '{}' }),
  createPvp: () => request<CreatePvpResponse>('/draft/pvp', { method: 'POST', body: '{}' }),
  joinPvp: (roomCode: string) =>
    request<{ session_id: string }>(`/draft/pvp/${roomCode}/join`, { method: 'POST', body: '{}' }),
  getState: (sessionId: string) => request<SessionState>(`/draft/${sessionId}`),
  reveal: (sessionId: string) => request<RevealResponse>(`/draft/${sessionId}/reveal`, { method: 'POST', body: '{}' }),
  decide: (sessionId: string, action: 'take' | 'skip') =>
    request<DecideResponse>(`/draft/${sessionId}/decide`, { method: 'POST', body: JSON.stringify({ action }) }),
  getResult: (sessionId: string) => request<ResultResponse>(`/draft/${sessionId}/result`),
  getLeaderboard: (scope: 'season' | 'alltime') => request<LeaderboardResponse>(`/leaderboard?scope=${scope}`),
}
