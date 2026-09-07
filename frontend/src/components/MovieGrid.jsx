import { FAVORITES, useSaved, WATCH_LATER } from '../context/SavedContext.jsx'
import MovieCard from './MovieCard.jsx'

// The grid reads the saved lists itself, so every page that shows films gets the
// right button labels without passing them down. Whether there is anything worth
// drawing stays the page's decision.
export default function MovieGrid({ movies }) {
  const { ids, toggle } = useSaved()

  return (
    <ul className="card-grid">
      {movies.map((movie) => (
        <MovieCard
          key={movie.tmdb_id}
          movie={movie}
          isFavorite={ids[FAVORITES].has(movie.tmdb_id)}
          isWatchLater={ids[WATCH_LATER].has(movie.tmdb_id)}
          onToggleFavorite={() => toggle(FAVORITES, movie)}
          onToggleWatchLater={() => toggle(WATCH_LATER, movie)}
        />
      ))}
    </ul>
  )
}
