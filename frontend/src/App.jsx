import { useState } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AuthModal from './components/AuthModal.jsx'
import Header from './components/Header.jsx'
import Favorites from './pages/Favorites.jsx'
import Search from './pages/Search.jsx'

export default function App() {
  // Held here rather than in Header: step 19 moves it into AuthContext, so that
  // any authenticated-only action on a page can open the same dialog.
  const [authOpen, setAuthOpen] = useState(false)

  return (
    <BrowserRouter>
      <Header onSignIn={() => setAuthOpen(true)} />

      <main>
        <Routes>
          <Route path="/" element={<Search />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="*" element={<h1>Page not found</h1>} />
        </Routes>
      </main>

      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </BrowserRouter>
  )
}
