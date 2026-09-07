import { FAVORITES } from '../context/SavedContext.jsx'
import SavedPage from './SavedPage.jsx'

export default function Favorites() {
  return <SavedPage title="Favorites" list={FAVORITES} />
}
