import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import Favorites from './pages/Favorites.jsx'
import Search from './pages/Search.jsx'

// The nav is temporary: step 5 replaces it with <Header />, which adds the auth controls.
export default function App() {
  return (
    <BrowserRouter>
      <header>
        <nav aria-label="Main">
          <NavLink to="/" end>
            Search
          </NavLink>
          <NavLink to="/favorites">Favorites</NavLink>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Search />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="*" element={<h1>Page not found</h1>} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
