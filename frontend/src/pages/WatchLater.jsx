import { WATCH_LATER } from '../context/SavedContext.jsx'
import SavedPage from './SavedPage.jsx'

export default function WatchLater() {
  return <SavedPage title="Watch later" list={WATCH_LATER} />
}
