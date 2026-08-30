import { useState } from 'react'
import type { User } from '../types'

export function HomeScreen({
  user, onSolo, onPvp, onJoinCode, onLeaderboard, busy,
}: {
  user: User
  onSolo: () => void
  onPvp: () => void
  onJoinCode: (code: string) => void
  onLeaderboard: () => void
  busy: boolean
}) {
  const [joinCode, setJoinCode] = useState('')

  return (
    <div className="screen">
      <div>
        <h1 className="title">Привет, {user.first_name}! ⚽</h1>
        <p className="subtitle">Собери мечту-состав из 5 игроков</p>
      </div>

      <div className="card stack">
        <div className="subtitle">Всего очков</div>
        <div style={{ fontSize: 20, fontWeight: 800 }}>{user.total_score}</div>
      </div>

      <div className="stack">
        <button className="btn btn-primary" disabled={busy} onClick={onSolo}>
          🎲 Играть соло
        </button>
        <button className="btn btn-secondary" disabled={busy} onClick={onPvp}>
          👥 Создать комнату с другом
        </button>
      </div>

      <div className="card stack">
        <div className="subtitle">Есть код комнаты?</div>
        <div className="btn-row">
          <input
            className="input"
            placeholder="ABCD1234"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            maxLength={8}
          />
          <button
            className="btn btn-secondary"
            disabled={busy || joinCode.length < 4}
            onClick={() => onJoinCode(joinCode.trim())}
          >
            Войти
          </button>
        </div>
      </div>

      <button className="btn btn-secondary" onClick={onLeaderboard}>
        🏆 Лидерборд
      </button>
    </div>
  )
}
