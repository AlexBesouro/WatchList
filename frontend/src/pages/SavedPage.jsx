import { Link } from 'react-router-dom'
import MovieGrid from '../components/MovieGrid.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useSaved } from '../context/SavedContext.jsx'

// Favorites and watch-later are the same screen over a different list, so they
// are one component called twice rather than two files kept in step by hand.
export default function SavedPage({ title, list }) {
  const { user, openAuth } = useAuth()
  const { lists, status, error } = useSaved()

  const movies = lists[list]
  const saved = status === 'ready' && movies.length > 0
  const isEmpty = status === 'ready' && movies.length === 0

  return (
    <>
      <h1>{title}</h1>

      <div aria-live="polite">
        {/* "idle" is the signed-out state: there is no list to load, which is
            not the same thing as a list that came back empty. */}
        {status === 'idle' && !user && (
          <p>
            <button type="button" onClick={openAuth}>
              Sign in
            </button>{' '}
            to keep your own {title.toLowerCase()} list.
          </p>
        )}
        {status === 'loading' && <p>Loading…</p>}
        {status === 'error' && <p className="error">{error}</p>}
        {error && status !== 'error' && <p className="error">{error}</p>}
        {isEmpty && (
          <p>
            Nothing here yet. <Link to="/">Find a film</Link> and add it.
          </p>
        )}
        {saved && (
          <p>
            {movies.length} film{movies.length > 1 ? 's' : ''} saved.
          </p>
        )}
      </div>

      {saved && <MovieGrid movies={movies} />}
    </>
  )
}
