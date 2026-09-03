import { useState } from 'react'
import { MOVIES } from '../api/fixtures.js'
import MovieCard from '../components/MovieCard.jsx'

export default function Search() {
  const [movies, setMovies] = useState(MOVIES)

  // Stands in for POST/DELETE on /to-watch/; step 19 replaces it with real calls.
  function toggleFavorite(movie) {
    setMovies((current) =>
      current.map((m) =>
        m.tmdb_id === movie.tmdb_id ? { ...m, watch_later: !m.watch_later } : m,
      ),
    )
  }

  return (
    <>
      <h1>Search</h1>

      <ul className="card-grid">
        {movies.map((movie) => (
          <MovieCard key={movie.tmdb_id} movie={movie} onToggle={toggleFavorite} />
        ))}
      </ul>
    </>
  )
}
