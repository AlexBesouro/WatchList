import { useState } from 'react'

const STORAGE_KEY = 'theme'

// The bootstrap script in index.html already resolved saved choice vs system
// preference, so <html data-theme> is the source of truth, not localStorage.
function readTheme() {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'
}

export function useTheme() {
  const [theme, setTheme] = useState(readTheme)

  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark'
    document.documentElement.dataset.theme = next
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Blocked site data: the choice just does not survive a reload.
    }
    setTheme(next)
  }

  return { theme, toggle }
}
