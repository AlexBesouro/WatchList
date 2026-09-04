// Mirrors backend/app/utils.py:9-21 rule for rule. The server stays the
// authority; this only tells the user what is missing before they submit.

// Hoisted out of the rule: a literal inside the function would build a new
// RegExp per call, and without the g flag one shared instance carries no state.
const SPECIAL = /[!@#$%^&*(),.?":{}|<>_-]/

const RULES = [
  { id: 'length', label: 'At least 8 characters', test: (value) => value.length >= 8 },
  { id: 'upper', label: 'One uppercase letter', test: (value) => /[A-Z]/.test(value) },
  { id: 'lower', label: 'One lowercase letter', test: (value) => /[a-z]/.test(value) },
  { id: 'digit', label: 'One digit', test: (value) => /\d/.test(value) },
  { id: 'special', label: 'One special character', test: (value) => SPECIAL.test(value) },
]

// Every rule with its current verdict, always in the order above, so the
// checklist never reorders itself while the user is typing.
export function checkPassword(value) {
  return RULES.map(({ id, label, test }) => ({ id, label, met: test(value) }))
}

// Reads the same RULES rather than counting checkPassword's results: one source,
// so the submit guard and the checklist cannot disagree.
export function isStrongPassword(value) {
  return RULES.every((rule) => rule.test(value))
}
