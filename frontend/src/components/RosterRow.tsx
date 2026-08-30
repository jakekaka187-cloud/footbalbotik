import type { RosterEntry } from '../types'
import { Avatar } from './Avatar'
import { ratingTier } from './PlayerCard'

export function RosterRow({ entry }: { entry: RosterEntry }) {
  const tier = ratingTier(entry.player.rating)
  return (
    <div className="roster-row">
      <div className="roster-row-avatar">
        <Avatar playerId={entry.player.id} size={36} />
      </div>
      <div>
        <div className="roster-row-name">{entry.player.name}</div>
        <div className="roster-row-meta">{entry.player.position} · {entry.player.club}</div>
      </div>
      <div className={`roster-row-badge tier-${tier}`}>{entry.player.rating}</div>
    </div>
  )
}
