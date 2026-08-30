import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import { Spinner } from '../components/Spinner'
import type { LeaderboardResponse } from '../types'

const MEDALS = ['🥇', '🥈', '🥉']

export function LeaderboardScreen({ onBack, onError }: { onBack: () => void; onError: (msg: string) => void }) {
  const [scope, setScope] = useState<'season' | 'alltime'>('season')
  const [data, setData] = useState<LeaderboardResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getLeaderboard(scope)
      .then(setData)
      .catch((e) => onError(e instanceof ApiError ? e.message : 'Не удалось загрузить лидерборд'))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope])

  return (
    <div className="screen">
      <h1 className="title">🏆 Лидерборд</h1>

      <div className="tabs">
        <div className={`tab ${scope === 'season' ? 'active' : ''}`} onClick={() => setScope('season')}>
          Конкурс
        </div>
        <div className={`tab ${scope === 'alltime' ? 'active' : ''}`} onClick={() => setScope('alltime')}>
          Всё время
        </div>
      </div>

      {loading ? (
        <Spinner />
      ) : data && data.rows.length > 0 ? (
        <div className="stack">
          {data.rows.map((row, i) => (
            <div key={row.telegram_id} className="roster-row">
              <div style={{ width: 28, fontWeight: 800, textAlign: 'center' }}>{MEDALS[i] ?? i + 1}</div>
              <div className="roster-row-name">{row.username ?? row.first_name}</div>
              <div className="roster-row-meta">{row.score} оч.</div>
            </div>
          ))}
        </div>
      ) : (
        <p className="subtitle">
          {scope === 'season'
            ? `Пока никто не набрал ${data?.competition_min_drafts ?? 3}+ завершённых драфтов`
            : 'Пока никто не играл'}
        </p>
      )}

      <button className="btn btn-secondary" onClick={onBack}>Назад</button>
    </div>
  )
}
