import { useEffect, useState } from 'react'

// Owns the loading / ready / error triple shared by every page that shows films.
// `loader` is an async function called once after mounting; `reload` runs another
// one later, from an event handler. Emptiness is not a status here — a page
// derives it from movies.length, which cannot fall out of step with the list.
export function useMovieList(loader) {
  const [status, setStatus] = useState('loading')
  const [movies, setMovies] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    // The effect callback cannot be async: React reads its return value as the
    // cleanup function, and an async function always returns a promise.
    async function first() {
      try {
        const found = await loader()
        if (ignore) return
        setMovies(found)
        setStatus('ready')
      } catch (failure) {
        if (ignore) return
        setError(failure.message)
        setStatus('error')
      }
    }

    first()

    // Drops the answer to a mount that no longer exists: StrictMode remounts
    // once in development, and a slow response can outlive the page.
    return () => {
      ignore = true
    }
    // `loader` must be defined outside the component so the reference is stable;
    // an inline arrow would be a new function on every render.
  }, [loader])

  async function reload(nextLoader) {
    setStatus('loading')
    try {
      setMovies(await nextLoader())
      setStatus('ready')
    } catch (failure) {
      setError(failure.message)
      setStatus('error')
    }
  }

  return { status, movies, error, setMovies, reload }
}
