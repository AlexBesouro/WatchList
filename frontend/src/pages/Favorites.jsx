import { Link } from 'react-router-dom'
import { MOVIES } from '../api/fixtures.js'
import MovieGrid from '../components/MovieGrid.jsx'
import { useMovieList } from '../hooks/useMovieList.js'

// Stands in for GET /to-watch/ until step 19. Declared outside the component:
// useMovieList takes it as an effect dependency, so the reference must be stable.
function fakeFavorites() {
  const found = MOVIES.filter((movie) => movie.is_favorite)
  return new Promise((resolve) => setTimeout(() => resolve(found), 400))
}

export default function Favorites() {
  // No reload here: this list is fetched once and then only shrinks locally.
  const { status, movies, error, setMovies } = useMovieList(fakeFavorites)

  // Stands in for DELETE /to-watch/{tmdb_id}; step 19 replaces it with a real call.
  function remove(movie) {
    setMovies((current) => current.filter((m) => m.tmdb_id !== movie.tmdb_id))
  }

  const saved = status === 'ready' && movies.length > 0
  const isEmpty = status === 'ready' && movies.length === 0

  return (
    <>
      <h1>Favorites</h1>

      <div aria-live="polite">
        {status === 'loading' && <p>Loading…</p>}
        {status === 'error' && <p className="error">{error}</p>}
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

      {saved && <MovieGrid movies={movies} onToggle={remove} />}
    </>
  )
}
