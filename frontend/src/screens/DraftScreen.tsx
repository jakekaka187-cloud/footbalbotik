import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api'
import { PlayerCard } from '../components/PlayerCard'
import { SlotProgressStrip } from '../components/SlotProgressStrip'
import { Spinner } from '../components/Spinner'
import { haptic } from '../telegram'
import type { SessionState } from '../types'

const SLOT_TITLE: Record<string, string> = {
  GK: 'Вратарь',
  DEF: 'Защитник',
  MID1: 'Полузащитник',
  MID2: 'Полузащитник',
  FWD: 'Нападающий',
}

export function DraftScreen({ sessionId, onFinished, onError }: {
  sessionId: string
  onFinished: () => void
  onError: (msg: string) => void
}) {
  const [state, setState] = useState<SessionState | null>(null)
  const [busy, setBusy] = useState(false)
  const [skipFlash, setSkipFlash] = useState<string | null>(null)
  const busyRef = useRef(false)

  async function refresh() {
    try {
      const s = await api.getState(sessionId)
      setState(s)
      if (s.status === 'finished') {
        onFinished()
      }
    } catch (e) {
      onError(e instanceof ApiError ? e.message : 'Не удалось загрузить сессию')
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  useEffect(() => {
    if (!state || state.mode !== 'pvp' || state.status !== 'active') return
    const interval = setInterval(() => {
      if (!busyRef.current) refresh()
    }, 1500)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state?.mode, state?.status, sessionId])

  useEffect(() => {
    if (!state?.me) return
    if (state.me.status === 'drafting' && !state.me.pending_candidate && !busy) {
      void reveal()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state?.me?.current_slot_index, state?.me?.pending_candidate])

  async function reveal() {
    setBusy(true)
    busyRef.current = true
    try {
      const res = await api.reveal(sessionId)
      setState((prev) =>
        prev && prev.me
          ? { ...prev, me: { ...prev.me, pending_candidate: { slot: res.slot, player: res.player } } }
          : prev
      )
    } catch (e) {
      onError(e instanceof ApiError ? e.message : 'Не удалось показать игрока')
    } finally {
      setBusy(false)
      busyRef.current = false
    }
  }

  async function decide(action: 'take' | 'skip') {
    if (!state?.me) return
    haptic(action === 'take' ? 'medium' : 'light')
    setBusy(true)
    busyRef.current = true
    try {
      const res = await api.decide(sessionId, action)
      if (res.skipped_player) {
        setSkipFlash(`${res.skipped_player.name} → ${res.committed_player.name}`)
        setTimeout(() => setSkipFlash(null), 1600)
      } else if (res.alt_player) {
        setSkipFlash(`Вторым мог быть: ${res.alt_player.name} (${res.alt_player.rating})`)
        setTimeout(() => setSkipFlash(null), 2200)
      }
      const s = await api.getState(sessionId)
      setState(s)
      if (s.status === 'finished') {
        onFinished()
      }
    } catch (e) {
      onError(e instanceof ApiError ? e.message : 'Не удалось сделать выбор')
    } finally {
      setBusy(false)
      busyRef.current = false
    }
  }

  if (!state || !state.me) {
    return (
      <div className="screen center">
        <Spinner />
      </div>
    )
  }

  const { me, opponent, slots } = state
  const candidate = me.pending_candidate

  if (me.status === 'done') {
    return (
      <div className="screen center">
        <div style={{ fontSize: 48 }}>✅</div>
        <h1 className="title">Состав собран!</h1>
        {state.mode === 'pvp' ? (
          <>
            <Spinner />
            <p className="subtitle">
              {opponent?.status === 'done' ? 'Финализируем результат…' : 'Ждём, пока соперник закончит…'}
            </p>
          </>
        ) : (
          <Spinner />
        )}
      </div>
    )
  }

  return (
    <div className="screen">
      <SlotProgressStrip slots={slots} currentIndex={me.current_slot_index} roster={me.roster} />

      {state.mode === 'pvp' && opponent && (
        <div className="subtitle" style={{ textAlign: 'center' }}>
          Соперник: {opponent.current_slot_index}/5 позиций
        </div>
      )}

      {skipFlash && <div className="error-banner" style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}>{skipFlash}</div>}

      <div>
        <p className="subtitle" style={{ textAlign: 'center', marginBottom: 8 }}>
          Позиция: {SLOT_TITLE[me.pending_candidate?.slot ?? slots[me.current_slot_index]]}
        </p>
        {candidate ? (
          <PlayerCard player={candidate.player} />
        ) : (
          <div className="center" style={{ minHeight: 160 }}>
            <Spinner />
          </div>
        )}
      </div>

      <div className="btn-row">
        <button className="btn btn-secondary" disabled={busy || !candidate} onClick={() => decide('skip')}>
          🔄 Другой
        </button>
        <button className="btn btn-primary" disabled={busy || !candidate} onClick={() => decide('take')}>
          ✅ Взять
        </button>
      </div>
    </div>
  )
}
