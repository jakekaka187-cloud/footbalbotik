import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import { FormationPitch } from '../components/FormationPitch'
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
      </div>

      <div className="stack">
        {me && <FormationPitch roster={me.roster} label={opponent ? 'Твой состав' : undefined} rating={me.team_rating} />}
        {opponent && <FormationPitch roster={opponent.roster} label="Состав соперника" rating={opponent.team_rating} />}
      </div>

      <div className="btn-row">
        <button className="btn btn-secondary" onClick={onHome}>🏠 В меню</button>
        <button className="btn btn-primary" onClick={onPlayAgain}>🔁 Ещё раз</button>
      </div>
    </div>
  )
}
