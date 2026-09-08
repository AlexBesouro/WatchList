import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MovieCard from './MovieCard.jsx'

const ARRIVAL = {
  tmdb_id: 329865,
  title: 'Arrival',
  release_date: '2016-11-11',
  poster_path: '/arrival.jpg',
  imdb_id: 'tt2543164',
  imdb_rating: 7.9,
}

function show(movie = ARRIVAL, props = {}) {
  return render(
    <MovieCard
      movie={movie}
      isFavorite={false}
      isWatchLater={false}
      onToggleFavorite={() => {}}
      onToggleWatchLater={() => {}}
      {...props}
    />,
  )
}

describe('what the card shows', () => {
  it('prints the title, the year and the IMDb rating', () => {
    show()

    expect(screen.getByRole('heading', { name: 'Arrival' })).toBeDefined()
    expect(screen.getByText(/2016/)).toBeDefined()
    expect(screen.getByText(/IMDb 7\.9/)).toBeDefined()
  })

  // Both cases are in the real data: TMDB has films with no poster, and OMDB
  // does not carry a rating for every title.
  it('still renders a film with no date and no rating', () => {
    const { container } = show({
      ...ARRIVAL,
      release_date: null,
      poster_path: null,
      imdb_rating: null,
    })

    expect(screen.getByText(/no IMDb rating/)).toBeDefined()
    // querySelector and not getByRole('img'): the poster carries alt="", which
    // hides it from the accessibility tree on purpose — the title is right below.
    expect(container.querySelector('img').getAttribute('src')).toBe('/placeholder.png')
  })
})

describe('the two save buttons', () => {
  it('says what clicking will do, and reports the saved state', () => {
    show(ARRIVAL, { isFavorite: true })

    const favorite = screen.getByRole('button', { name: 'Remove from favorites' })
    // aria-pressed is what a screen reader announces and what the stylesheet
    // reads, so asserting it covers both at once.
    expect(favorite.getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Watch later' })).toBeDefined()
  })

  it('calls the handler that belongs to the button clicked', async () => {
    const onToggleFavorite = vi.fn()
    const onToggleWatchLater = vi.fn()
    show(ARRIVAL, { onToggleFavorite, onToggleWatchLater })

    await userEvent.click(screen.getByRole('button', { name: 'Add to favorites' }))

    expect(onToggleFavorite).toHaveBeenCalledTimes(1)
    expect(onToggleWatchLater).not.toHaveBeenCalled()
  })

  // The saved label names the action, not the state: on the Watch later page
  // every card is saved, and "In watch later" told nobody how to take it back.
  it('offers to remove a film already in watch later', () => {
    show(ARRIVAL, { isWatchLater: true })

    const watchLater = screen.getByRole('button', { name: 'Remove from watch later' })
    expect(watchLater.getAttribute('aria-pressed')).toBe('true')
  })
})
