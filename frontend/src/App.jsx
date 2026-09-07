import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AuthModal from './components/AuthModal.jsx'
import Header from './components/Header.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { SavedProvider } from './context/SavedContext.jsx'
import Favorites from './pages/Favorites.jsx'
import Search from './pages/Search.jsx'
import WatchLater from './pages/WatchLater.jsx'

// SavedProvider sits inside AuthProvider because it reads the token: a provider
// can only use a context that is already open above it.
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SavedProvider>
          <Header />

          <main>
            <Routes>
              <Route path="/" element={<Search />} />
              <Route path="/favorites" element={<Favorites />} />
              <Route path="/watch-later" element={<WatchLater />} />
              <Route path="*" element={<h1>Page not found</h1>} />
            </Routes>
          </main>

          {/* Mounted once, outside the routes: any page can open it, and it
              stays on screen when the route under it changes. */}
          <AuthModal />
        </SavedProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
