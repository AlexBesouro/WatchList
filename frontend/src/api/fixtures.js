// Mirrors the GET /movies/ payload field for field, including already_seen and
// personal_rating, which this SPA never shows — a trimmed fixture hides surprises.
export const MOVIES = [
  {
    tmdb_id: 550,
    title: 'Fight Club',
    release_date: '1999-10-15',
    poster_path: '/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
    imdb_id: 'tt0137523',
    imdb_rating: 8.8,
    already_seen: false,
    personal_rating: 0,
    watch_later: false,
  },
  {
    // No poster: TMDB leaves poster_path null for plenty of titles.
    tmdb_id: 680,
    title: 'Pulp Fiction',
    release_date: '1994-09-10',
    poster_path: null,
    imdb_id: 'tt0110912',
    imdb_rating: 8.9,
    already_seen: false,
    personal_rating: 0,
    watch_later: true,
  },
  {
    // Absent from OMDB: both IMDb fields come back null.
    tmdb_id: 13,
    title: 'Forrest Gump',
    release_date: '1994-06-23',
    poster_path: '/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg',
    imdb_id: null,
    imdb_rating: null,
    already_seen: false,
    personal_rating: 0,
    watch_later: false,
  },
  {
    tmdb_id: 155,
    title: 'The Dark Knight',
    release_date: '2008-07-16',
    poster_path: '/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
    imdb_id: 'tt0468569',
    imdb_rating: 9,
    already_seen: false,
    personal_rating: 0,
    watch_later: false,
  },
]
