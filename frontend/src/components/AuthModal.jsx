import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { checkPassword, isStrongPassword } from '../lib/password.js'

const EMPTY = { email: '', password: '', first_name: '', last_name: '' }

export default function AuthModal() {
  const { authOpen, closeAuth, signIn, signUp } = useAuth()

  const dialogRef = useRef(null)
  const [mode, setMode] = useState('signin')
  const [form, setForm] = useState(EMPTY)
  const [notice, setNotice] = useState('')
  const [pending, setPending] = useState(false)

  const signup = mode === 'signup'

  // Bridges the declarative prop to the imperative DOM API. showModal() throws
  // if the dialog is already open, hence the guards.
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (authOpen && !dialog.open) dialog.showModal()
    if (!authOpen && dialog.open) dialog.close()
  }, [authOpen])

  // One handler for every field: the property name comes from the input's name.
  function update(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  function switchMode(next) {
    setMode(next)
    setNotice('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    // Native validation covers required and length; the rest of the policy is here.
    if (signup && !isStrongPassword(form.password)) {
      setNotice('The password does not meet every rule yet.')
      return
    }

    setPending(true)
    setNotice('')
    try {
      // The two calls differ, what happens after them does not: a token is
      // stored, the dialog closes and the saved lists load themselves.
      if (signup) await signUp(form)
      else await signIn({ email: form.email, password: form.password })

      setForm(EMPTY)
      closeAuth()
    } catch (failure) {
      // The message is the API's own `detail`, so "User with this email already
      // exists" reaches the user instead of a generic failure.
      setNotice(failure.message)
    } finally {
      setPending(false)
    }
  }

  // ::backdrop has no node of its own, so a click on it is reported with the
  // <dialog> as target, while a click inside always names a child.
  function handleBackdropClick(event) {
    if (event.target === dialogRef.current) dialogRef.current.close()
  }

  return (
    // onClose also fires for Escape, which closes the dialog without telling React.
    <dialog
      ref={dialogRef}
      onClose={closeAuth}
      onClick={handleBackdropClick}
      aria-labelledby="auth-title"
    >
      <div className="auth-body">
        <h2 id="auth-title">{signup ? 'Create an account' : 'Sign in'}</h2>

        <div className="auth-tabs">
          <button type="button" aria-pressed={!signup} onClick={() => switchMode('signin')}>
            Sign in
          </button>
          <button type="button" aria-pressed={signup} onClick={() => switchMode('signup')}>
            Create account
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={form.email}
              onChange={update}
            />
          </div>

          <div>
            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              name="password"
              type="password"
              autoComplete={signup ? 'new-password' : 'current-password'}
              required
              // Read out when focus lands on the field. Deliberately not aria-live,
              // which would announce the whole list on every keystroke.
              aria-describedby={signup ? 'password-rules' : undefined}
              value={form.password}
              onChange={update}
            />

            {signup && (
              <ul className="password-rules" id="password-rules">
                {checkPassword(form.password).map((rule) => (
                  <li key={rule.id} className={rule.met ? 'is-met' : undefined}>
                    <span aria-hidden="true">{rule.met ? '✓' : '·'}</span> {rule.label}
                    <span className="sr-only">{rule.met ? ' — met' : ' — not met'}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {signup && (
            <>
              <div>
                <label htmlFor="auth-first-name">First name</label>
                <input
                  id="auth-first-name"
                  name="first_name"
                  type="text"
                  autoComplete="given-name"
                  required
                  value={form.first_name}
                  onChange={update}
                />
              </div>

              <div>
                <label htmlFor="auth-last-name">Last name</label>
                <input
                  id="auth-last-name"
                  name="last_name"
                  type="text"
                  autoComplete="family-name"
                  required
                  value={form.last_name}
                  onChange={update}
                />
              </div>
            </>
          )}

          <p className="auth-notice" aria-live="polite">
            {notice}
          </p>

          <div className="auth-actions">
            <button type="button" onClick={closeAuth}>
              Cancel
            </button>
            {/* Disabled while the request is out: a second submit would create
                the account twice, and the second one answers 409. */}
            <button type="submit" disabled={pending}>
              {pending ? 'Working…' : signup ? 'Create account' : 'Sign in'}
            </button>
          </div>
        </form>
      </div>
    </dialog>
  )
}
