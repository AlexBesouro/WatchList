import { useEffect, useState } from 'react'
import { fetchMovies } from '../api/client.js'
import MovieGrid from '../components/MovieGrid.jsx'
import { useSaved } from '../context/SavedContext.jsx'

// TMDB answers with twenty films per page and never says how many pages exist,
// so a full page is the signal that another one probably follows.
const PAGE_SIZE = 20

// TMDB refuses anything past 500, and the API validates the same bound.
const LAST_PAGE = 500

export default function Search() {
  const [query, setQuery] = useState('')
  // The term whose results are on screen; "" means the popular list.
  const [submitted, setSubmitted] = useState('')
  const [page, setPage] = useState(1)

  const [status, setStatus] = useState('loading')
  const [movies, setMovies] = useState([])
  const [error, setError] = useState('')

  // The saved lists have their own failures — a duplicate, an expired token —
  // and they belong in the same live region as this page's own.
  const { error: savedError } = useSaved()

  // Runs on mount and again whenever the term or the page changes, so paging
  // and searching are the same code path rather than two.
  useEffect(() => {
    let ignore = false
    setStatus('loading')

    // The effect itself cannot be async: React reads what it returns as the
    // cleanup function, and an async function always returns a promise.
    async function load() {
      try {
        const found = await fetchMovies({ query: submitted, page })
        if (ignore) return
        setMovies(found)
        setStatus('ready')
      } catch (failure) {
        if (ignore) return
        setError(failure.message)
        setStatus('error')
      }
    }

    load()

    // Drops the answer to a request the user has already moved past: two quick
    // searches can come back out of order, and the last one must win.
    return () => {
      ignore = true
    }
  }, [submitted, page])

  function handleSubmit(event) {
    event.preventDefault()
    setSubmitted(query.trim())
    setPage(1)
  }

  const found = status === 'ready' && movies.length > 0
  const isEmpty = status === 'ready' && movies.length === 0

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
        {status === 'error' && <p className="error">{error}</p>}
        {savedError && <p className="error">{savedError}</p>}
        {isEmpty && <p>Nothing found for “{submitted}”.</p>}
        {found && submitted === '' && <p>Popular films.</p>}
        {found && submitted !== '' && (
          <p>
            Results for “{submitted}”, page {page}.
          </p>
        )}
      </div>

      {found && (
        <>
          <MovieGrid movies={movies} />

          <nav className="pagination" aria-label="Result pages">
            <button type="button" disabled={page === 1} onClick={() => setPage(page - 1)}>
              Previous
            </button>
            <span>Page {page}</span>
            <button
              type="button"
              disabled={movies.length < PAGE_SIZE || page >= LAST_PAGE}
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
