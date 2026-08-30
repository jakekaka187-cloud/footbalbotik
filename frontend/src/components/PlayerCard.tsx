import type { Player } from '../types'

export function ratingTier(rating: number): 'gold' | 'silver' | 'bronze' {
  if (rating >= 85) return 'gold'
  if (rating >= 74) return 'silver'
  return 'bronze'
}

export function PlayerCard({ player }: { player: Player }) {
  const tier = ratingTier(player.rating)
  return (
    <div className={`player-card tier-${tier}`}>
      <div className="player-card-rating">{player.rating}</div>
      <div className="player-card-position">{player.position}</div>
      <div className="player-card-name">{player.name}</div>
      <div className="player-card-meta">{player.nationality}</div>
      <div className="player-card-meta">{player.club}</div>
    </div>
  )
}
