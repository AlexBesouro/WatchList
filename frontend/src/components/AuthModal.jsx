import { useEffect, useRef, useState } from 'react'

const EMPTY = { email: '', password: '', first_name: '', last_name: '' }

export default function AuthModal({ open, onClose }) {
  const dialogRef = useRef(null)
  const [mode, setMode] = useState('signin')
  const [form, setForm] = useState(EMPTY)
  const [notice, setNotice] = useState('')

  // Bridges the declarative prop to the imperative DOM API. showModal() throws
  // if the dialog is already open, hence the guards.
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  // One handler for every field: the property name comes from the input's name.
  function update(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  function switchMode(next) {
    setMode(next)
    setNotice('')
  }

  function handleSubmit(event) {
    event.preventDefault()
    setNotice('Not connected to the API yet — that is step 19.')
  }

  // ::backdrop has no node of its own, so a click on it is reported with the
  // <dialog> as target, while a click inside always names a child. The dialog
  // carries no padding, so "target is the dialog" can only mean the backdrop.
  function handleBackdropClick(event) {
    if (event.target === dialogRef.current) dialogRef.current.close()
  }

  const signup = mode === 'signup'

  return (
    // onClose also fires for Escape, which closes the dialog without telling React.
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onClick={handleBackdropClick}
      aria-labelledby="auth-title"
    >
      <div className="auth-body">
        <h2 id="auth-title">{signup ? 'Create an account' : 'Sign in'}</h2>

        <div className="auth-tabs">
          <button
            type="button"
            aria-pressed={!signup}
            onClick={() => switchMode('signin')}
          >
            Sign in
          </button>
          <button
            type="button"
            aria-pressed={signup}
            onClick={() => switchMode('signup')}
          >
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
              value={form.password}
              onChange={update}
            />
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
            <button type="button" onClick={onClose}>
              Cancel
            </button>
            <button type="submit">{signup ? 'Create account' : 'Sign in'}</button>
          </div>
        </form>
      </div>
    </dialog>
  )
}
