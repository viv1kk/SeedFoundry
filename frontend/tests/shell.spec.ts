// App shell and routes (ui-spec.md section 1, D-38).

import { afterEach, describe, expect, it } from 'vitest'
import { emptySnapshot, mountApp } from './helpers'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('routes', () => {
  // D-43: /knowledge renders the Knowledge page from M3, so it left this placeholder table.
  // D-54 (h): /build/1 and /build/2 render the Build page from M6, so they left it too.
  // D-59: /review/1 and /review/2 render the Review page from M7, so they left it as well.
  // D-76: /seed renders the Seed page from M11, the last route to leave it.
  it('/seed renders the Seed page inside the shell, and says why it is empty before approval (D-76)', async () => {
    const { wrapper, router } = await mountApp('/seed', emptySnapshot())
    expect(router.currentRoute.value.name).toBe('seed')
    expect(wrapper.find('header [data-test="wordmark"]').exists()).toBe(true)
    expect(wrapper.find('nav[aria-label="Journey"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="seed"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="placeholder"]').exists()).toBe(false)
    expect(wrapper.find('main h1').text()).toBe('Seed')
    expect(wrapper.find('[data-test="seed-empty-reason"]').text()).toBe('No Seed is approved yet, so there are no Seed files to show.')
  })

  it('/knowledge renders the Knowledge page inside the shell (D-43)', async () => {
    const { wrapper, router } = await mountApp('/knowledge', emptySnapshot())
    expect(router.currentRoute.value.name).toBe('knowledge')
    expect(wrapper.find('header [data-test="wordmark"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="knowledge"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="file-panel"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="placeholder"]').exists()).toBe(false)
  })

  it.each([
    ['/build/1', 'Build, iteration 1'],
    ['/build/2', 'Build, iteration 2'],
  ])('%s renders the Build page inside the shell (D-54)', async (path, title) => {
    const { wrapper, router } = await mountApp(path, emptySnapshot())
    expect(router.currentRoute.value.name).toBe('build')
    expect(wrapper.find('header [data-test="wordmark"]').exists()).toBe(true)
    expect(wrapper.find('nav[aria-label="Journey"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="build"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="placeholder"]').exists()).toBe(false)
    expect(wrapper.find('main h1').text()).toBe(title)
  })

  it.each([
    ['/review/1', 'Review, iteration 1'],
    ['/review/2', 'Review, iteration 2'],
  ])('%s renders the Review page inside the shell (D-59)', async (path, title) => {
    const { wrapper, router } = await mountApp(path, emptySnapshot())
    expect(router.currentRoute.value.name).toBe('review')
    expect(wrapper.find('header [data-test="wordmark"]').exists()).toBe(true)
    expect(wrapper.find('nav[aria-label="Journey"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="review"]').exists()).toBe(true)
    expect(wrapper.find('main [data-test="placeholder"]').exists()).toBe(false)
    expect(wrapper.find('main h1').text()).toBe(title)
  })

  it('redirects / to /knowledge', async () => {
    const { router } = await mountApp('/')
    expect(router.currentRoute.value.fullPath).toBe('/knowledge')
  })

  it.each(['/nowhere', '/build/0', '/review/0', '/build', '/review/1/dashboard'])('redirects %s to /knowledge', async (path) => {
    const { router } = await mountApp(path)
    expect(router.currentRoute.value.fullPath).toBe('/knowledge')
  })

  it('keeps the dashboard as a query string on the review route (OQ-4)', async () => {
    const { wrapper, router } = await mountApp('/review/1?dashboard=license-optimization&drill=vendor')
    expect(router.currentRoute.value.name).toBe('review')
    expect(router.currentRoute.value.query).toEqual({ dashboard: 'license-optimization', drill: 'vendor' })
    expect(wrapper.find('main h1').text()).toBe('Review, iteration 1')
  })
})

describe('journey indicator', () => {
  it('lists Knowledge, Build, Review, Seed in order', async () => {
    const { wrapper } = await mountApp('/knowledge')
    expect(wrapper.findAll('nav[aria-label="Journey"] li').map((li) => li.text())).toEqual([
      'Knowledge',
      'Build',
      'Review',
      'Seed',
    ])
  })

  it.each([
    ['/knowledge', 'Knowledge'],
    ['/build/1', 'Build'],
    ['/review/2', 'Review'],
    ['/seed', 'Seed'],
  ])('marks the current step on %s', async (path, label) => {
    const { wrapper } = await mountApp(path)
    const current = wrapper.findAll('nav[aria-label="Journey"] [aria-current="step"]')
    expect(current.map((el) => el.text())).toEqual([label])
  })

  it('links Knowledge only; Build, Review and Seed are not links yet', async () => {
    const { wrapper } = await mountApp('/seed')
    const links = wrapper.findAll('nav[aria-label="Journey"] a')
    expect(links.map((a) => a.text())).toEqual(['Knowledge'])
    expect(links[0].attributes('href')).toBe('/knowledge')
  })

  it('links Seed too once a Seed is approved, and marks it reached (D-75)', async () => {
    const approved = emptySnapshot({ approval: { iteration: 2, build_id: 'b-2', approved_at: '2026-10-04T12:00:00.000+00:00' } })
    const { wrapper } = await mountApp('/knowledge', approved)
    const links = wrapper.findAll('nav[aria-label="Journey"] a')
    expect(links.map((a) => [a.text(), a.attributes('href')])).toEqual([
      ['Knowledge', '/knowledge'],
      ['Seed', '/seed'],
    ])
    expect(links[1].classes()).toContain('journey__step--done')
  })

  it('goes to Knowledge when Knowledge is clicked', async () => {
    const { wrapper, router } = await mountApp('/review/1')
    await wrapper.find('nav[aria-label="Journey"] a').trigger('click')
    await router.isReady()
    await new Promise((r) => setTimeout(r))
    expect(router.currentRoute.value.name).toBe('knowledge')
  })
})

describe('iteration badge', () => {
  it('is hidden before the first build', async () => {
    const { wrapper } = await mountApp('/knowledge', emptySnapshot())
    expect(wrapper.find('[data-test="iteration-badge"]').exists()).toBe(false)
  })

  it('is hidden before the snapshot arrives', async () => {
    const { wrapper } = await mountApp('/knowledge', null)
    expect(wrapper.find('[data-test="iteration-badge"]').exists()).toBe(false)
  })

  it('reads "Iteration 1" once a build exists, with no total (D-80)', async () => {
    const snapshot = emptySnapshot({ seq: 4, builds: [{ id: 'b-1', iteration: 1, status: 'running' }] })
    const { wrapper } = await mountApp('/build/1', snapshot)
    const badge = wrapper.find('header [data-test="iteration-badge"]')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('Iteration 1')
  })

  it("shows the latest build's iteration", async () => {
    const snapshot = emptySnapshot({
      iteration: 2,
      builds: [
        { id: 'b-1', iteration: 1, status: 'completed' },
        { id: 'b-2', iteration: 2, status: 'running' },
      ],
    })
    const { wrapper } = await mountApp('/build/2', snapshot)
    expect(wrapper.find('[data-test="iteration-badge"]').text()).toBe('Iteration 2')
  })
})

describe('top bar', () => {
  it('holds the wordmark left, the journey centre, and the badge and theme toggle right', async () => {
    const snapshot = emptySnapshot({ builds: [{ id: 'b-1', iteration: 1, status: 'completed' }] })
    const { wrapper } = await mountApp('/knowledge', snapshot)
    const columns = wrapper.find('header.top-bar').element.children
    expect(columns).toHaveLength(3)
    expect(columns[0].textContent?.trim()).toBe('SeedFoundry')
    expect(columns[1].matches('nav[aria-label="Journey"]')).toBe(true)
    expect(columns[2].querySelector('[data-test="iteration-badge"]')).not.toBeNull()
    expect(columns[2].querySelector('[data-test="theme-toggle"]')).not.toBeNull()
  })

  it('every control is a native button or link, so it is keyboard reachable', async () => {
    const { wrapper } = await mountApp('/knowledge')
    const controls = wrapper.findAll('header a, header button')
    expect(controls.length).toBeGreaterThanOrEqual(2)
    for (const control of controls) expect(control.attributes('tabindex')).not.toBe('-1')
  })
})
