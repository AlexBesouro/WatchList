import MovieCard from './MovieCard.jsx'

// Markup only: whether there is anything worth drawing is the page's decision.
export default function MovieGrid({ movies, onToggle }) {
  return (
    <ul className="card-grid">
      {movies.map((movie) => (
        <MovieCard key={movie.tmdb_id} movie={movie} onToggle={onToggle} />
      ))}
    </ul>
  )
}
