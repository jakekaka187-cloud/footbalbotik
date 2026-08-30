import type { RosterEntry, Slot } from '../types'

const SLOT_LABEL: Record<Slot, string> = {
  GK: 'ВРТ',
  DEF: 'ЗАЩ',
  MID1: 'ПЗ',
  MID2: 'ПЗ',
  FWD: 'НАП',
}

export function SlotProgressStrip({
  slots, currentIndex, roster,
}: {
  slots: Slot[]
  currentIndex: number
  roster: RosterEntry[]
}) {
  return (
    <div className="slot-strip">
      {slots.map((slot, i) => {
        const filled = roster.find((r) => r.slot === slot)
        const isCurrent = i === currentIndex && !filled
        return (
          <div key={`${slot}-${i}`} className={`slot-pip ${filled ? 'filled' : ''} ${isCurrent ? 'current' : ''}`}>
            <span className="slot-pip-label">{SLOT_LABEL[slot]}</span>
            <span>{filled ? filled.player.rating : i < currentIndex ? '—' : '?'}</span>
          </div>
        )
      })}
    </div>
  )
}
