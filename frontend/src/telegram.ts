interface TelegramWebApp {
  initData: string
  initDataUnsafe: { start_param?: string; user?: { id: number; first_name: string } }
  ready: () => void
  expand: () => void
  close: () => void
  setHeaderColor: (color: string) => void
  setBackgroundColor: (color: string) => void
  themeParams: Record<string, string>
  colorScheme: 'light' | 'dark'
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
  }
  BackButton: {
    show: () => void
    hide: () => void
    onClick: (cb: () => void) => void
    offClick: (cb: () => void) => void
  }
  shareURL?: (url: string, text?: string) => void
  openTelegramLink?: (url: string) => void
}

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp }
  }
}

const webApp = window.Telegram?.WebApp

export function initTelegram() {
  webApp?.ready()
  webApp?.expand()
}

export function getInitData(): string {
  return webApp?.initData ?? ''
}

export function getStartParam(): string | null {
  return webApp?.initDataUnsafe?.start_param ?? null
}

export function haptic(style: 'light' | 'medium' | 'heavy' = 'medium') {
  webApp?.HapticFeedback?.impactOccurred(style)
}

export function shareInviteLink(url: string, text: string) {
  if (webApp?.shareURL) {
    webApp.shareURL(url, text)
    return
  }
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`
  if (webApp?.openTelegramLink) {
    webApp.openTelegramLink(shareUrl)
  } else {
    window.open(shareUrl, '_blank')
  }
}

export function setBackButton(onClick: (() => void) | null) {
  if (!webApp) return
  if (onClick) {
    webApp.BackButton.show()
    webApp.BackButton.onClick(onClick)
  } else {
    webApp.BackButton.hide()
  }
}

export const isInsideTelegram = Boolean(webApp?.initData)

// --- Local dev only: lets you test in a plain browser (two tabs = two players)
// against a backend started with DEV_MODE=1. Has no effect inside real Telegram.
function devParam(name: string): string | null {
  return new URLSearchParams(window.location.search).get(name)
}

export function getDevUserId(): string {
  const fromUrl = devParam('dev_uid')
  if (fromUrl) return fromUrl
  let stored = window.localStorage.getItem('dev_uid')
  if (!stored) {
    stored = String(900000 + Math.floor(Math.random() * 99999))
    window.localStorage.setItem('dev_uid', stored)
  }
  return stored
}

export function getDevStartParam(): string | null {
  return devParam('dev_start')
}
