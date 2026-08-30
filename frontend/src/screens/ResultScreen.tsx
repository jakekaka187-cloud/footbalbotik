import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import { RosterRow } from '../components/RosterRow'
import { Spinner } from '../components/Spinner'
import type { ResultResponse } from '../types'

export function ResultScreen({
  sessionId, myTelegramId, onPlayAgain, onHome, onError,
}: {
  sessionId: string
  myTelegramId: number
  onPlayAgain: () => void
  onHome: () => void
  onError: (msg: string) => void
}) {
  const [result, setResult] = useState<ResultResponse | null>(null)

  useEffect(() => {
    api.getResult(sessionId)
      .then(setResult)
      .catch((e) => onError(e instanceof ApiError ? e.message : 'Не удалось загрузить результат'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  if (!result) {
    return (
      <div className="screen center">
        <Spinner />
      </div>
    )
  }

  const me = result.participants.find((p) => p.telegram_id === myTelegramId)
  const opponent = result.participants.find((p) => p.telegram_id !== myTelegramId)

  return (
    <div className="screen">
      <div className="center" style={{ flex: 'none' }}>
        <div style={{ fontSize: 40 }}>🏆</div>
        <h1 className="title">Состав готов!</h1>
        {me && <p className="subtitle">Общий рейтинг: {me.team_rating} (средний {me.team_ovr_avg})</p>}
      </div>

      {opponent ? (
        <div className="compare-columns">
          <div className="stack">
            <div className="subtitle" style={{ textAlign: 'center' }}>Ты · {me?.team_rating}</div>
            {me?.roster.map((r, i) => <RosterRow key={i} entry={r} />)}
          </div>
          <div className="stack">
            <div className="subtitle" style={{ textAlign: 'center' }}>Соперник · {opponent.team_rating}</div>
            {opponent.roster.map((r, i) => <RosterRow key={i} entry={r} />)}
          </div>
        </div>
      ) : (
        <div className="stack">
          {me?.roster.map((r, i) => <RosterRow key={i} entry={r} />)}
        </div>
      )}

      <div className="btn-row">
        <button className="btn btn-secondary" onClick={onHome}>🏠 В меню</button>
        <button className="btn btn-primary" onClick={onPlayAgain}>🔁 Ещё раз</button>
      </div>
    </div>
  )
}
