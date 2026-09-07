import { useState } from 'react'

// TMDB serves posters from its own CDN. w200 is the smallest width that stays
// sharp on a card, so it is requested instead of the original file.
const POSTER_BASE = 'https://image.tmdb.org/t/p/w200'

// Vite serves the contents of public/ at the site root, so the URL is absolute
// and carries no "public" segment.
const POSTER_PLACEHOLDER = '/placeholder.png'

// Props only, no context: the card is the piece the tests drive directly, and
// it renders the same whether the data came from the API or from a fixture.
export default function MovieCard({
  movie,
  isFavorite,
  isWatchLater,
  onToggleFavorite,
  onToggleWatchLater,
}) {
  const [posterFailed, setPosterFailed] = useState(false)

  const year = movie.release_date ? movie.release_date.slice(0, 4) : '—'
  const hasPoster = movie.poster_path && !posterFailed

  return (
    <li className="card">
      <img
        className="card-poster"
        src={hasPoster ? POSTER_BASE + movie.poster_path : POSTER_PLACEHOLDER}
        // The title sits right below, so a described poster would be read twice.
        alt=""
        width="200"
        height="300"
        loading="lazy"
        onError={() => setPosterFailed(true)}
      />

      <h2 className="card-title">{movie.title}</h2>

      <p className="card-meta">
        {year} ·{' '}
        {movie.imdb_rating == null ? 'no IMDb rating' : `IMDb ${movie.imdb_rating}`}
      </p>

      {/* aria-pressed and not a class alone: the button is a switch, and its
          state has to reach a screen reader as well as the stylesheet. */}
      <div className="card-actions">
        <button type="button" aria-pressed={isFavorite} onClick={onToggleFavorite}>
          {isFavorite ? 'In favorites' : 'Add to favorites'}
        </button>
        <button type="button" aria-pressed={isWatchLater} onClick={onToggleWatchLater}>
          {isWatchLater ? 'In watch later' : 'Watch later'}
        </button>
      </div>
    </li>
  )
}
