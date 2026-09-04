import { useState } from 'react'

// TMDB serves posters from its own CDN. w200 is the smallest width that stays
// sharp on a card, so it is requested instead of the original file.
const POSTER_BASE = 'https://image.tmdb.org/t/p/w200'

// Vite serves the contents of public/ at the site root, so the URL is absolute
// and carries no "public" segment.
const POSTER_PLACEHOLDER = '/placeholder.png'

export default function MovieCard({ movie, onToggle }) {
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

      <button
        type="button"
        className={movie.watch_later ? 'is-active' : undefined}
        onClick={() => onToggle(movie)}
      >
        {movie.watch_later ? 'Remove from favourites' : 'Add to favourites'}
      </button>
    </li>
  )
}
