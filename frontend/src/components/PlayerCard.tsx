import type { Player } from '../types'
import { Avatar } from './Avatar'

export function ratingTier(rating: number): 'gold' | 'silver' | 'bronze' {
  if (rating >= 85) return 'gold'
  if (rating >= 74) return 'silver'
  return 'bronze'
}

const POSITION_ABBR: Record<string, string> = {
  'Вратарь': 'GK',
  'Защитник': 'DF',
  'Полузащитник': 'MF',
  'Нападающий': 'FW',
}

export function PlayerCard({ player }: { player: Player }) {
  const tier = ratingTier(player.rating)
  const flag = player.nationality.split(' ')[0]
  return (
    <div className={`player-card tier-${tier}`}>
      <div className="player-card-top">
        <div className="player-card-rating">{player.rating}</div>
        <div className="player-card-pos-badge">
          <span>{flag}</span>
          <span>{POSITION_ABBR[player.position] ?? player.position}</span>
        </div>
      </div>
      <div className="player-card-photo">
        <Avatar playerId={player.id} size={76} />
      </div>
      <div className="player-card-name">{player.name}</div>
      <div className="player-card-meta">{player.club}</div>
    </div>
  )
}
