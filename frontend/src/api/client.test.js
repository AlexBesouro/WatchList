import { addSaved, ApiError, fetchMovies, removeSaved } from './client.js'

// fetch is replaced rather than a server started: these tests are about how the
// answer is read, not about whether the API is up.
function answer({ status = 200, body = null }) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
}

describe('the request the client sends', () => {
  it('leaves the query out when the term is empty', async () => {
    answer({ body: [] })

    await fetchMovies({ query: '', page: 2 })

    const [url] = globalThis.fetch.mock.calls[0]
    expect(url).toContain('/movies?page=2')
    expect(url).not.toContain('query')
  })

  it('sends the token as a Bearer header on a private call', async () => {
    answer({ status: 201, body: {} })

    await addSaved('a-token', 'favorites', { tmdb_id: 1 })

    const [url, options] = globalThis.fetch.mock.calls[0]
    expect(url).toMatch(/\/favorites$/)
    expect(options.headers.Authorization).toBe('Bearer a-token')
    expect(options.method).toBe('POST')
  })
})

describe('how a failure reaches the caller', () => {
  it('turns a 409 into an ApiError carrying the API detail', async () => {
    answer({ status: 409, body: { detail: 'This film is already in the list.' } })

    // The status is what the caller branches on; the message is what it shows.
    await expect(addSaved('a-token', 'favorites', { tmdb_id: 1 })).rejects.toMatchObject({
      name: 'ApiError',
      status: 409,
      message: 'This film is already in the list.',
    })
  })

  it('folds a 422 validation list into one sentence', async () => {
    answer({
      status: 422,
      body: { detail: [{ msg: 'String should have at least 3 characters' }] },
    })

    await expect(fetchMovies({ query: 'ab' })).rejects.toThrow(/at least 3 characters/)
  })

  it('reports an unreachable API as status 0', async () => {
    // fetch only rejects when the request never reached a server at all.
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(fetchMovies()).rejects.toMatchObject({ status: 0 })
  })
})

describe('an answer with no body', () => {
  it('reads 204 as null instead of trying to parse it', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json: async () => {
        throw new SyntaxError('Unexpected end of JSON input')
      },
    })

    await expect(removeSaved('a-token', 'favorites', 1)).resolves.toBeNull()
  })
})

describe('the error type itself', () => {
  it('is a real Error, so try/catch and .message work as usual', () => {
    const failure = new ApiError(401, 'Invalid credentials')

    expect(failure instanceof Error).toBe(true)
    expect(failure.message).toBe('Invalid credentials')
  })
})
