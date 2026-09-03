import { useEffect, useState } from 'react'
import { MOVIES } from '../api/fixtures.js'
import MovieCard from '../components/MovieCard.jsx'

// Two per page, so four fixture films are enough to exercise the pagination.
const PAGE_SIZE = 2

// Stands in for GET /movies/ until step 19. An empty term means "popular", which
// every title matches. "boom" is the only way to reach the error state by hand.
function fakeSearch(term) {
  if (term === 'boom') {
    return Promise.reject(new Error('The server did not answer. Try again.'))
  }
  const found = MOVIES.filter((movie) =>
    movie.title.toLowerCase().includes(term.toLowerCase()),
  )
  return new Promise((resolve) => setTimeout(() => resolve(found), 400))
}

export default function Search() {
  const [query, setQuery] = useState('')
  // The term whose results are on screen; "" means the popular list.
  const [submitted, setSubmitted] = useState('')
  const [status, setStatus] = useState('loading')
  const [movies, setMovies] = useState([])
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)

  async function load(term) {
    setStatus('loading')
    setPage(1)
    try {
      const found = await fakeSearch(term)
      setMovies(found)
      setSubmitted(term)
      setStatus(found.length > 0 ? 'ready' : 'empty')
    } catch (failure) {
      setError(failure.message)
      setStatus('error')
    }
  }

  // Empty dependency array: the popular list is fetched once, after mounting.
  useEffect(() => {
    load('')
  }, [])

  function handleSubmit(event) {
    event.preventDefault()
    load(query.trim())
  }

  // Stands in for POST/DELETE on /to-watch/; step 19 replaces it with real calls.
  function toggleFavorite(movie) {
    setMovies((current) =>
      current.map((m) =>
        m.tmdb_id === movie.tmdb_id ? { ...m, watch_later: !m.watch_later } : m,
      ),
    )
  }

  // Derived from movies and page, so they are computed here rather than stored.
  const pageCount = Math.max(1, Math.ceil(movies.length / PAGE_SIZE))
  const shown = movies.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <>
      <h1>Search</h1>

      <form className="search-bar" onSubmit={handleSubmit}>
        <label htmlFor="query">Film title</label>
        {/* minLength blocks a 1-2 letter submit in the browser itself; an empty
            field is exempt from the rule, which is what loads the popular list. */}
        <input
          id="query"
          name="query"
          type="search"
          minLength={3}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      {/* Always in the DOM: a live region announces changes inside a node that
          already exists, not the arrival of the node itself. */}
      <div aria-live="polite">
        {status === 'loading' && <p>Loading…</p>}
        {status === 'empty' && <p>Nothing found for “{submitted}”.</p>}
        {status === 'error' && <p className="error">{error}</p>}
        {status === 'ready' && submitted === '' && <p>Popular films.</p>}
        {status === 'ready' && submitted !== '' && (
          <p>
            {movies.length} film{movies.length > 1 ? 's' : ''} found for “
            {submitted}”.
          </p>
        )}
      </div>

      {status === 'ready' && (
        <>
          <ul className="card-grid">
            {shown.map((movie) => (
              <MovieCard
                key={movie.tmdb_id}
                movie={movie}
                onToggle={toggleFavorite}
              />
            ))}
          </ul>

          <nav className="pagination" aria-label="Result pages">
            <button
              type="button"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </button>
            <span>
              Page {page} of {pageCount}
            </span>
            <button
              type="button"
              disabled={page === pageCount}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </nav>
        </>
      )}
    </>
  )
}
