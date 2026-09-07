import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  test: {
    // The components under test touch the DOM, which Node does not have.
    environment: 'jsdom',
    // Also what lets Testing Library unmount between tests on its own; without
    // it the second test finds the first one's markup still on the page.
    globals: true,
  },
})
