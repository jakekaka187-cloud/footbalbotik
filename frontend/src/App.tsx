import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from './api'
import { GateScreen } from './screens/GateScreen'
import { HomeScreen } from './screens/HomeScreen'
import { PvpLobbyScreen } from './screens/PvpLobbyScreen'
import { DraftScreen } from './screens/DraftScreen'
import { ResultScreen } from './screens/ResultScreen'
import { LeaderboardScreen } from './screens/LeaderboardScreen'
import { Spinner } from './components/Spinner'
import { getDevStartParam, getStartParam, initTelegram, isInsideTelegram } from './telegram'
import type { AuthResponse, CreatePvpResponse } from './types'

type View = 'loading' | 'gate' | 'home' | 'pvpLobby' | 'draft' | 'result' | 'leaderboard'

export default function App() {
  const [view, setView] = useState<View>('loading')
  const [auth, setAuth] = useState<AuthResponse | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [pvpRoom, setPvpRoom] = useState<CreatePvpResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const lobbyPoll = useRef<number | null>(null)

  function fail(msg: string) {
    setError(msg)
  }

  async function bootstrap() {
    setView('loading')
    try {
      const res = await api.auth()
      setAuth(res)
      if (!res.subscribed) {
        setView('gate')
        return
      }

      const startParam = isInsideTelegram ? getStartParam() : getDevStartParam()
      if (startParam && !startParam.startsWith('ref_')) {
        const roomCode = startParam.toUpperCase()
        try {
          const joined = await api.joinPvp(roomCode)
          setSessionId(joined.session_id)
          setView('draft')
          return
        } catch (e) {
          if (e instanceof ApiError && e.status === 409) {
            // Already a participant (e.g. creator reopening their own invite link) —
            // check the room's actual status rather than assuming it's playable yet.
            try {
              const state = await api.getState(roomCode)
              setSessionId(roomCode)
              if (state.status === 'waiting') {
                enterPvpLobby({
                  session_id: roomCode, mode: 'pvp', status: 'waiting', room_code: roomCode,
                  invite_link: state.invite_link ?? '', expires_at: '',
                })
              } else {
                setView('draft')
              }
              return
            } catch (e2) {
              fail(e2 instanceof ApiError ? e2.message : 'Не удалось открыть комнату')
              return
            }
          }
          fail(e instanceof ApiError ? e.message : 'Не удалось присоединиться к комнате')
        }
      }
      setView('home')
    } catch (e) {
      fail(e instanceof ApiError ? e.message : 'Не удалось подключиться к серверу')
    }
  }

  useEffect(() => {
    initTelegram()
    void bootstrap()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function stopLobbyPoll() {
    if (lobbyPoll.current) {
      window.clearInterval(lobbyPoll.current)
      lobbyPoll.current = null
    }
  }

  async function startSolo() {
    setBusy(true)
    try {
      const res = await api.createSolo()
      setSessionId(res.session_id)
      setView('draft')
    } catch (e) {
      fail(e instanceof ApiError ? e.message : 'Не удалось начать игру')
    } finally {
      setBusy(false)
    }
  }

  function enterPvpLobby(room: CreatePvpResponse) {
    setSessionId(room.session_id)
    setPvpRoom(room)
    setView('pvpLobby')
    lobbyPoll.current = window.setInterval(async () => {
      try {
        const state = await api.getState(room.session_id)
        if (state.status === 'active') {
          stopLobbyPoll()
          setView('draft')
        }
      } catch {
        // keep polling silently
      }
    }, 2000)
  }

  async function startPvp() {
    setBusy(true)
    try {
      const room = await api.createPvp()
      enterPvpLobby(room)
    } catch (e) {
      fail(e instanceof ApiError ? e.message : 'Не удалось создать комнату')
    } finally {
      setBusy(false)
    }
  }

  async function joinByCode(code: string) {
    setBusy(true)
    try {
      const joined = await api.joinPvp(code)
      setSessionId(joined.session_id)
      setView('draft')
    } catch (e) {
      fail(e instanceof ApiError ? e.message : 'Комната не найдена')
    } finally {
      setBusy(false)
    }
  }

  function goHome() {
    stopLobbyPoll()
    setSessionId(null)
    setPvpRoom(null)
    setView('home')
  }

  if (error) {
    return (
      <div className="screen center">
        <div className="error-banner">{error}</div>
        <button className="btn btn-primary" onClick={() => { setError(null); void bootstrap() }}>
          Повторить
        </button>
      </div>
    )
  }

  if (view === 'loading' || !auth) {
    return (
      <div className="screen center">
        <Spinner />
      </div>
    )
  }

  if (view === 'gate') {
    return <GateScreen channelUsername={auth.channel_username} onRecheck={() => void bootstrap()} />
  }

  if (view === 'pvpLobby' && pvpRoom) {
    return <PvpLobbyScreen room={pvpRoom} onCancel={goHome} />
  }

  if (view === 'draft' && sessionId) {
    return (
      <DraftScreen
        sessionId={sessionId}
        onFinished={() => setView('result')}
        onError={fail}
      />
    )
  }

  if (view === 'result' && sessionId) {
    return (
      <ResultScreen
        sessionId={sessionId}
        myTelegramId={auth.user.telegram_id}
        onPlayAgain={goHome}
        onHome={goHome}
        onError={fail}
      />
    )
  }

  if (view === 'leaderboard') {
    return <LeaderboardScreen onBack={() => setView('home')} onError={fail} />
  }

  return (
    <HomeScreen
      user={auth.user}
      busy={busy}
      onSolo={() => void startSolo()}
      onPvp={() => void startPvp()}
      onJoinCode={(code) => void joinByCode(code)}
      onLeaderboard={() => setView('leaderboard')}
    />
  )
}
