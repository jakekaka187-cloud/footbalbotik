import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api'
import { FormationPitch } from '../components/FormationPitch'
import { Spinner } from '../components/Spinner'
import type { ResultResponse } from '../types'

export function ResultScreen({
  sessionId, myTelegramId, onEnterSession, onHome, onError,
}: {
  sessionId: string
  myTelegramId: number
  onEnterSession: (sessionId: string) => void
  onHome: () => void
  onError: (msg: string) => void
}) {
  const [result, setResult] = useState<ResultResponse | null>(null)
  const [waitingRematch, setWaitingRematch] = useState(false)
  const [busy, setBusy] = useState(false)
  const rematchPoll = useRef<number | null>(null)

  useEffect(() => {
    api.getResult(sessionId)
      .then(setResult)
      .catch((e) => onError(e instanceof ApiError ? e.message : 'Не удалось загрузить результат'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  useEffect(() => () => {
    if (rematchPoll.current) window.clearInterval(rematchPoll.current)
  }, [])

  async function playAgain() {
    if (!result) return
    if (result.mode === 'solo') {
      setBusy(true)
      try {
        const session = await api.createSolo()
        onEnterSession(session.session_id)
      } catch (e) {
        onError(e instanceof ApiError ? e.message : 'Не удалось начать игру')
      } finally {
        setBusy(false)
      }
      return
    }

    // pvp — ask for a rematch, poll until the opponent also asks
    setBusy(true)
    try {
      const res = await api.rematch(sessionId)
      if (res.status === 'matched' && res.session_id) {
        onEnterSession(res.session_id)
        return
      }
      setWaitingRematch(true)
      rematchPoll.current = window.setInterval(async () => {
        try {
          const poll = await api.rematch(sessionId)
          if (poll.status === 'matched' && poll.session_id) {
            if (rematchPoll.current) window.clearInterval(rematchPoll.current)
            onEnterSession(poll.session_id)
          }
        } catch {
          // keep polling silently
        }
      }, 2000)
    } catch (e) {
      onError(e instanceof ApiError ? e.message : 'Не удалось запросить реванш')
    } finally {
      setBusy(false)
    }
  }

  if (!result) {
    return (
      <div className="screen center">
        <Spinner />
      </div>
    )
  }

  const me = result.participants.find((p) => p.telegram_id === myTelegramId)
  const opponent = result.participants.find((p) => p.telegram_id !== myTelegramId)

  if (waitingRematch) {
    return (
      <div className="screen center">
        <Spinner />
        <p className="subtitle">Ждём, согласится ли соперник на реванш…</p>
        <button className="btn btn-secondary" onClick={onHome}>Отмена</button>
      </div>
    )
  }

  return (
    <div className="screen">
      <div className="center" style={{ flex: 'none' }}>
        <div style={{ fontSize: 40 }}>🏆</div>
        <h1 className="title">Состав готов!</h1>
      </div>

      <div className="stack">
        {me && <FormationPitch roster={me.roster} label={opponent ? 'Твой состав' : undefined} rating={me.team_rating} />}
        {opponent && <FormationPitch roster={opponent.roster} label="Состав соперника" rating={opponent.team_rating} />}
      </div>

      <div className="btn-row">
        <button className="btn btn-secondary" onClick={onHome}>🏠 В меню</button>
        <button className="btn btn-primary" disabled={busy} onClick={playAgain}>🔁 Ещё раз</button>
      </div>
    </div>
  )
}
