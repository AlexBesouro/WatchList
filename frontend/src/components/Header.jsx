import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useTheme } from '../hooks/useTheme.js'

export default function Header() {
  const { theme, toggle } = useTheme()
  const { user, signOut, openAuth } = useAuth()

  return (
    <header>
      <Link to="/" className="wordmark">
        WatchList
      </Link>

      <nav aria-label="Main">
        {/* `end` on the home link only: without it "/" matches every route and
            two links would claim to be the current page at once. */}
        <NavLink to="/" end>
          Search
        </NavLink>
        <NavLink to="/favorites">Favorites</NavLink>
        <NavLink to="/watch-later">Watch later</NavLink>
      </nav>

      <div className="header-actions">
        <button type="button" onClick={toggle}>
          {theme === 'dark' ? 'Light theme' : 'Dark theme'}
        </button>

        {user ? (
          <>
            {/* The address, not the first name: it is what was typed to sign
                in, so it answers "which account am I on" without ambiguity. */}
            <span className="signed-in">{user.email}</span>
            <button type="button" onClick={signOut}>
              Sign out
            </button>
          </>
        ) : (
          <button type="button" onClick={openAuth}>
            Sign in
          </button>
        )}
      </div>
    </header>
  )
}
