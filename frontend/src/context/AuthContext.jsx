import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { fetchMe, signIn as apiSignIn, signUp as apiSignUp } from '../api/client.js'

const AuthContext = createContext(null)

// Namespaced: localStorage is shared by every page served from this origin.
const TOKEN_KEY = 'watchlist.token'

function readToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    // A private window can refuse storage entirely; the session then lasts
    // until the tab is closed, which is a working app, not a broken one.
    return null
  }
}

export function AuthProvider({ children }) {
  // The lazy initialiser runs once, on the first render, instead of on all of them.
  const [token, setToken] = useState(readToken)
  const [user, setUser] = useState(null)
  const [authOpen, setAuthOpen] = useState(false)

  const signOut = useCallback(() => {
    setToken(null)
    setUser(null)
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      // Nothing was stored in the first place.
    }
  }, [])

  // A token from localStorage may be expired, or signed by a server that has
  // since changed its key. /users/me is what turns it back into a session.
  useEffect(() => {
    if (!token) {
      setUser(null)
      return
    }
    let ignore = false

    async function load() {
      try {
        const me = await fetchMe(token)
        if (!ignore) setUser(me)
      } catch {
        if (!ignore) signOut()
      }
    }

    load()

    return () => {
      ignore = true
    }
  }, [token, signOut])

  function keep(accessToken) {
    try {
      localStorage.setItem(TOKEN_KEY, accessToken)
    } catch {
      // The session still works, it just will not survive a reload.
    }
    setToken(accessToken)
  }

  async function signIn(credentials) {
    const { access_token } = await apiSignIn(credentials)
    keep(access_token)
  }

  // Sign-up does not return a token, so the account is created and then used
  // immediately: one action for the user, two calls underneath.
  async function signUp(form) {
    await apiSignUp(form)
    await signIn({ email: form.email, password: form.password })
  }

  const value = {
    token,
    user,
    signIn,
    signUp,
    signOut,
    authOpen,
    openAuth: () => setAuthOpen(true),
    closeAuth: () => setAuthOpen(false),
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  // Fails loudly at the first render instead of silently reading undefined
  // fields off null further down the tree.
  if (!value) throw new Error('useAuth must be used inside <AuthProvider>')
  return value
}
