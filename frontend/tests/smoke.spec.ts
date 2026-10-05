import { describe, expect, it } from 'vitest'
import { mountApp } from './helpers'

// M0 smoke test. Its assertion was changed in M2 by D-39: the app now mounts with its router
// inside the shell, and the shell's wordmark carries the name the placeholder h1 used to.
describe('M0 smoke', () => {
  it('renders the app with its name', async () => {
    const { wrapper } = await mountApp('/')
    expect(wrapper.find('[data-test="wordmark"]').text()).toBe('SeedFactory')
    wrapper.unmount()
  })
})
