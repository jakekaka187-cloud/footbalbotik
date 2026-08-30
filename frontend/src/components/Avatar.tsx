// Neutral, generated flat-icon "face" for a player card — deterministic per
// player id (same player always renders the same way), not a likeness of
// any real person.

const SKIN_TONES = ['#f4d3ab', '#e3b287', '#c68a5f', '#a06a3d', '#6e4527']
const HAIR_COLORS = ['#1c1c1c', '#3a2314', '#6b4a2b', '#0a0a0a', '#8a6a4a']
// How far down the hair circle is allowed to show (in svg units, head circle
// is cy=34 r=26) — all values stay well above the eyes at y=32 so hair can
// never cover the face.
const HAIR_HEIGHTS = [16, 20, 24]

function seeded(id: number, salt: number): number {
  const x = Math.sin(id * 12.9898 + salt * 78.233) * 43758.5453
  return x - Math.floor(x)
}

export function Avatar({ playerId, size = 72 }: { playerId: number; size?: number }) {
  const skin = SKIN_TONES[playerId % SKIN_TONES.length]
  const hairRoll = seeded(playerId, 3.1)
  const hasHair = hairRoll > 0.15
  const hairColor = HAIR_COLORS[Math.floor(seeded(playerId, 7.7) * HAIR_COLORS.length)]
  const hairHeight = HAIR_HEIGHTS[Math.floor(seeded(playerId, 11.3) * HAIR_HEIGHTS.length)]
  const clipId = `hair-clip-${playerId}`

  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-hidden="true">
      <circle cx="32" cy="34" r="26" fill={skin} />
      <circle cx="23" cy="32" r="2.6" fill="#2a2a2a" />
      <circle cx="41" cy="32" r="2.6" fill="#2a2a2a" />
      <path d="M23 42 Q32 49 41 42" stroke="#2a2a2a" strokeWidth="2.6" fill="none" strokeLinecap="round" />
      {hasHair && (
        <>
          <clipPath id={clipId}>
            <rect x="0" y="0" width="64" height={hairHeight} />
          </clipPath>
          <circle cx="32" cy="20" r="24" fill={hairColor} clipPath={`url(#${clipId})`} />
        </>
      )}
    </svg>
  )
}
