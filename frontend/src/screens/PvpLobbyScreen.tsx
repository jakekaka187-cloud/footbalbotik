import { shareInviteLink } from '../telegram'
import { Spinner } from '../components/Spinner'
import type { CreatePvpResponse } from '../types'

export function PvpLobbyScreen({ room, onCancel }: { room: CreatePvpResponse; onCancel: () => void }) {
  return (
    <div className="screen">
      <div>
        <h1 className="title">Комната создана</h1>
        <p className="subtitle">Отправь код или ссылку другу — игра начнётся, как только он присоединится</p>
      </div>

      <div className="code-badge">{room.room_code}</div>

      <button
        className="btn btn-primary"
        onClick={() => shareInviteLink(room.invite_link, 'Го собирать состав! ⚽')}
      >
        📤 Отправить приглашение
      </button>

      <div className="center">
        <Spinner />
        <span className="subtitle">Ждём друга…</span>
      </div>

      <button className="btn btn-secondary" onClick={onCancel}>
        Отмена
      </button>
    </div>
  )
}
