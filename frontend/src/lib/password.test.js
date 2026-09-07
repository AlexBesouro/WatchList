import { checkPassword, isStrongPassword } from './password.js'

// The five rules mirror backend/app/utils.py. If one side changes and the other
// does not, the checklist starts lying about what the server will accept.
describe('the live checklist', () => {
  it('always returns the five rules, in the same order', () => {
    const rules = checkPassword('')

    expect(rules.map((rule) => rule.id)).toEqual([
      'length',
      'upper',
      'lower',
      'digit',
      'special',
    ])
    expect(rules.every((rule) => rule.met)).toBe(false)
  })

  it('marks only the rules the value actually meets', () => {
    const met = checkPassword('lowercase').filter((rule) => rule.met)

    expect(met.map((rule) => rule.id)).toEqual(['length', 'lower'])
  })
})

describe('the submit guard', () => {
  it('accepts a password that meets every rule', () => {
    expect(isStrongPassword('Password_1')).toBe(true)
  })

  it.each([
    ['Pass_1', 'too short'],
    ['password_1', 'no uppercase'],
    ['PASSWORD_1', 'no lowercase'],
    ['Password_', 'no digit'],
    ['Password1', 'no special character'],
  ])('refuses %s (%s)', (value) => {
    expect(isStrongPassword(value)).toBe(false)
  })
})
