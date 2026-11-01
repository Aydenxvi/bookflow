/**
 * Minimal typed surface over the Telegram WebApp SDK, plus the detection
 * logic that decides between real Telegram auth and browser demo mode.
 *
 * We don't pull in a wrapper npm package for this — the SDK is loaded as a
 * global via the <script src="https://telegram.org/js/telegram-web-app.js">
 * tag in index.html (the official, recommended way to include it), and the
 * surface we actually use is small enough to type by hand.
 */

export interface TelegramWebAppUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
  photo_url?: string
}

export interface TelegramWebApp {
  initData: string
  initDataUnsafe: { user?: TelegramWebAppUser; start_param?: string; auth_date?: number }
  platform: string
  colorScheme: 'light' | 'dark'
  themeParams: Record<string, string>
  isExpanded: boolean
  viewportHeight: number
  ready: () => void
  expand: () => void
  close: () => void
  enableClosingConfirmation: () => void
  setHeaderColor: (color: string) => void
  setBackgroundColor: (color: string) => void
  onEvent: (event: string, cb: () => void) => void
  offEvent: (event: string, cb: () => void) => void
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
  }
  BackButton?: {
    isVisible: boolean
    show: () => void
    hide: () => void
    onClick: (cb: () => void) => void
    offClick: (cb: () => void) => void
  }
  MainButton?: {
    text: string
    isVisible: boolean
    isActive: boolean
    show: () => void
    hide: () => void
    enable: () => void
    disable: () => void
    setText: (text: string) => void
    onClick: (cb: () => void) => void
    offClick: (cb: () => void) => void
  }
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp }
  }
}

/**
 * Real Telegram clients always populate `initData` with a signed, non-empty
 * string once the Mini App has launched. A plain browser tab — even with
 * the SDK script loaded, since it degrades gracefully outside Telegram —
 * will have the WebApp object but an empty `initData`. That's the signal we
 * use to fall back to demo mode rather than just checking for the object's
 * existence.
 */
export function getTelegramWebApp(): TelegramWebApp | null {
  if (typeof window === 'undefined') return null
  const webApp = window.Telegram?.WebApp
  if (!webApp || !webApp.initData) return null
  return webApp
}

export function isRunningInTelegram(): boolean {
  return getTelegramWebApp() !== null
}
