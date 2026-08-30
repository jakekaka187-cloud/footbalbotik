import type { RosterEntry } from '../types'
import { ratingTier } from './PlayerCard'

export function RosterRow({ entry }: { entry: RosterEntry }) {
  const tier = ratingTier(entry.player.rating)
  return (
    <div className="roster-row">
      <div className={`roster-row-badge tier-${tier}`}>{entry.player.rating}</div>
      <div>
        <div className="roster-row-name">{entry.player.name}</div>
        <div className="roster-row-meta">{entry.player.position} · {entry.player.club}</div>
      </div>
    </div>
  )
}
