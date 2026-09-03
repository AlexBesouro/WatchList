import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Header from './components/Header.jsx'
import Favorites from './pages/Favorites.jsx'
import Search from './pages/Search.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Header />

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
