import type { RosterEntry, Slot } from '../types'
import { Avatar } from './Avatar'
import { ratingTier } from './PlayerCard'

const SLOT_COORDS: Record<Slot, { top: string; left: string }> = {
  FWD: { top: '12%', left: '50%' },
  MID1: { top: '42%', left: '26%' },
  MID2: { top: '42%', left: '74%' },
  DEF: { top: '68%', left: '50%' },
  GK: { top: '90%', left: '50%' },
}

export function FormationPitch({ roster, label, rating }: {
  roster: RosterEntry[]
  label?: string
  rating?: number
}) {
  return (
    <div className="pitch-wrap">
      {(label || rating !== undefined) && (
        <div className="pitch-header">
          {label && <span>{label}</span>}
          {rating !== undefined && <span className="pitch-rating">{rating}</span>}
        </div>
      )}
      <div className="pitch">
        <div className="pitch-circle" />
        {roster.map((entry) => {
          const coords = SLOT_COORDS[entry.slot]
          const tier = ratingTier(entry.player.rating)
          const shortName = entry.player.name.trim().split(/\s+/).pop() ?? entry.player.name
          return (
            <div key={entry.slot} className="pitch-player" style={{ top: coords.top, left: coords.left }}>
              <div className={`pitch-player-avatar tier-${tier}`}>
                <Avatar playerId={entry.player.id} size={38} />
              </div>
              <div className="pitch-player-rating">{entry.player.rating}</div>
              <div className="pitch-player-name">{shortName}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
