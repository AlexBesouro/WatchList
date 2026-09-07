import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { addSaved, fetchSaved, removeSaved } from '../api/client.js'
import { useAuth } from './AuthContext.jsx'

const SavedContext = createContext(null)

// The same two names the back-end uses as route prefixes.
export const FAVORITES = 'favorites'
export const WATCH_LATER = 'watch-later'

const EMPTY = { [FAVORITES]: [], [WATCH_LATER]: [] }

// Both saved lists live here rather than on their pages: the Search page has to
// know what is already saved to label its buttons, and one owner means the two
// screens can never disagree about it.
export function SavedProvider({ children }) {
  const { token, openAuth } = useAuth()
  const [lists, setLists] = useState(EMPTY)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) {
      setLists(EMPTY)
      setStatus('idle')
      return
    }
    let ignore = false
    setStatus('loading')
    setError('')

    // Both lists at once: they are independent, so waiting for one before
    // asking for the other would double the time the page takes to settle.
    Promise.all([fetchSaved(token, FAVORITES), fetchSaved(token, WATCH_LATER)])
      .then(([favorites, watchLater]) => {
        if (ignore) return
        setLists({ [FAVORITES]: favorites, [WATCH_LATER]: watchLater })
        setStatus('ready')
      })
      .catch((failure) => {
        if (ignore) return
        setError(failure.message)
        setStatus('error')
      })

    // Drops the answer to a session that no longer exists: signing out while a
    // request is in flight would otherwise repopulate the lists after it.
    return () => {
      ignore = true
    }
  }, [token])

  // Sets, not .some() on every card: a page of twenty films asks forty times.
  const ids = useMemo(
    () => ({
      [FAVORITES]: new Set(lists[FAVORITES].map((movie) => movie.tmdb_id)),
      [WATCH_LATER]: new Set(lists[WATCH_LATER].map((movie) => movie.tmdb_id)),
    }),
    [lists],
  )

  async function toggle(list, movie) {
    // The only place the app asks for an account: saving a film, never browsing.
    if (!token) {
      openAuth()
      return
    }
    setError('')

    try {
      if (ids[list].has(movie.tmdb_id)) {
        await removeSaved(token, list, movie.tmdb_id)
        setLists((current) => ({
          ...current,
          [list]: current[list].filter((saved) => saved.tmdb_id !== movie.tmdb_id),
        }))
      } else {
        // The row the API returns, not the card that was clicked: what the
        // server stored is what the saved page must show.
        const created = await addSaved(token, list, movie)
        setLists((current) => ({ ...current, [list]: [...current[list], created] }))
      }
    } catch (failure) {
      setError(failure.message)
    }
  }

  const value = { lists, ids, status, error, toggle }

  return <SavedContext.Provider value={value}>{children}</SavedContext.Provider>
}

export function useSaved() {
  const value = useContext(SavedContext)
  if (!value) throw new Error('useSaved must be used inside <SavedProvider>')
  return value
}
