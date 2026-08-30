export function GateScreen({ channelUsername, onRecheck }: { channelUsername: string; onRecheck: () => void }) {
  const handle = channelUsername.replace('@', '')
  return (
    <div className="screen center">
      <div style={{ fontSize: 48 }}>🔒</div>
      <h1 className="title">Доступ закрыт</h1>
      <p className="subtitle">Чтобы играть в футбольный драфт — подпишись на канал {channelUsername}</p>
      <div className="stack" style={{ width: '100%' }}>
        <a
          className="btn btn-primary"
          style={{ textAlign: 'center', textDecoration: 'none', display: 'block' }}
          href={`https://t.me/${handle}`}
          target="_blank"
          rel="noreferrer"
        >
          📢 Подписаться
        </a>
        <button className="btn btn-secondary" onClick={onRecheck}>
          ✅ Я подписался
        </button>
      </div>
    </div>
  )
}
