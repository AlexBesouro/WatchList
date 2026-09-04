import { Link, NavLink } from 'react-router-dom'
import { useTheme } from '../hooks/useTheme.js'

export default function Header({ onSignIn }) {
  const { theme, toggle } = useTheme()

  return (
    <header>
      <Link to="/" className="wordmark">
        WatchList
      </Link>

      <nav aria-label="Main">
        <NavLink to="/" end>
          Search
        </NavLink>
        <NavLink to="/favorites">Favorites</NavLink>
      </nav>

      <div className="header-actions">
        <button type="button" onClick={toggle}>
          {theme === 'dark' ? 'Light theme' : 'Dark theme'}
        </button>
        <button type="button" onClick={onSignIn}>
          Sign in
        </button>
      </div>
    </header>
  )
}
