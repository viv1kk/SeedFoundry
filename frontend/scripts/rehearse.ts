// The rehearsal (M12, D-77): the whole demo in real headless Chrome, against an isolated copy of the
// app, with the network cut off. It checks what jsdom cannot: real rendering, real timing, real
// keyboard focus, and every request the page makes.
//
//   node scripts/rehearse.ts [--speed 1|2|4] [--out <folder>]      (npm run rehearse -- --speed 4)
//
// - An isolated copy: the backend on a spare port with a throwaway var/ and the offline guard
//   (backend/tests/offline_guard, which refuses and logs any host but loopback), and Vite on another
//   spare port proxying to it. The app at 127.0.0.1:5273 and var/ are never touched.
// - Chrome headless with a fresh profile and every host but 127.0.0.1 unresolvable. Every request the
//   page makes is logged; any that leaves 127.0.0.1 fails the run (NFR-2, AC-9).
// - The demo through the UI, with the operator's shortcuts: Load sample, Start Build, a reload mid-build,
//   the report, the dashboard, Reject with Prefill, iteration 2, Approve, the Seed page and its
//   downloads, a server restart, Reset (AC-1 to AC-10). Builds are timed by the wall clock (FR-B-6 at 1x),
//   dashboards from View Dashboard to every panel drawn (NFR-3), long tasks while the console streams,
//   and keystrokes in a 1 MB file.
// - Keyboard: on each page, Tab walks every control, and each shows a visible focus ring (NFR-6).
// - Screenshots of each page in both themes, and results.json, go to the out folder.
//
// Plain erasable TypeScript, so Node runs it without a build step. Needs Chrome (or CHROME=<path>)
// and the backend's environment (backend/.venv). Exits non-zero when a check fails.

import { spawn, spawnSync, type ChildProcess } from 'node:child_process'
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { createServer } from 'node:net'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const FRONTEND = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const ROOT = resolve(FRONTEND, '..')
const BACKEND = join(ROOT, 'backend')
const CATALOGUE = ['N-1', 'N-2', 'N-3', 'N-4', 'N-5', 'V-1', 'V-2', 'V-3', 'V-4', 'V-5', 'V-6', 'V-7', 'V-8', 'L-1']
const EM_DASH = String.fromCharCode(0x2014)
// A line of the 1 MB file: about a million bytes of these, under the limit with room to type (FR-IN-11).
const NOTE = '- A line of notes about a licence, long enough to fill a megabyte of markdown.\n'

// Options

const args = process.argv.slice(2)
function option(name: string, fallback: string): string {
  const at = args.indexOf(`--${name}`)
  return at >= 0 && args[at + 1] ? args[at + 1] : fallback
}
const SPEED = Number(option('speed', '1'))
if (![1, 2, 4].includes(SPEED)) throw new Error('--speed is 1, 2 or 4')
const WORK = mkdtempSync(join(tmpdir(), 'seedfoundry-rehearsal-'))
const OUT = resolve(option('out', join(WORK, 'out')))
mkdirSync(OUT, { recursive: true })

// Results

interface Check {
  id: string
  label: string
  pass: boolean
  detail: string
}
const checks: Check[] = []
const timings: Record<string, number> = {}
function check(id: string, label: string, pass: boolean, detail = ''): void {
  checks.push({ id, label, pass, detail })
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${id.padEnd(8)} ${label}${detail ? `: ${detail}` : ''}`)
}
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

// Processes

const children: ChildProcess[] = []

function freePort(): Promise<number> {
  return new Promise((done, fail) => {
    const server = createServer()
    server.once('error', fail)
    server.listen(0, '127.0.0.1', () => {
      const address = server.address()
      server.close(() => done(typeof address === 'object' && address ? address.port : 0))
    })
  })
}

function start(command: string, argv: string[], cwd: string, env: Record<string, string>): ChildProcess {
  const child = spawn(command, argv, { cwd, env: { ...process.env, ...env }, stdio: 'ignore', windowsHide: true })
  children.push(child)
  return child
}

function stop(child: ChildProcess): void {
  if (child.exitCode !== null || child.pid === undefined) return
  if (process.platform === 'win32') spawnSync('taskkill', ['/T', '/F', '/PID', String(child.pid)], { stdio: 'ignore' })
  else child.kill('SIGKILL')
}

async function answers(url: string): Promise<boolean> {
  try {
    return (await fetch(url, { signal: AbortSignal.timeout(1000) })).ok
  } catch {
    return false
  }
}

async function waitUntil<T>(what: string, probe: () => Promise<T | null | false | undefined>, seconds: number, every = 250): Promise<T> {
  const deadline = Date.now() + seconds * 1000
  for (;;) {
    const found = await probe()
    if (found) return found
    if (Date.now() > deadline) throw new Error(`timed out after ${seconds} s waiting for ${what}`)
    await sleep(every)
  }
}

const python = join(BACKEND, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const VAR = join(WORK, 'var')
const OFFLINE_LOG = join(WORK, 'offline.log')
let apiPort = 0
let backend: ChildProcess

async function startBackend(): Promise<void> {
  backend = start(python, ['-m', 'uvicorn', 'seedfoundry.main:app', '--host', '127.0.0.1', '--port', String(apiPort), '--timeout-graceful-shutdown', '2'], BACKEND, {
    SEEDFOUNDRY_VAR_DIR: VAR,
    PYTHONPATH: join(BACKEND, 'tests', 'offline_guard'),
    SEEDFOUNDRY_OFFLINE_LOG: OFFLINE_LOG,
  })
  await waitUntil('the backend', () => answers(`http://127.0.0.1:${apiPort}/api/health`), 60)
}

function findChrome(): string {
  const candidates = [
    process.env.CHROME ?? '',
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    '/usr/bin/google-chrome',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ]
  const found = candidates.find((path) => path && existsSync(path))
  if (!found) throw new Error('No Chrome found. Set CHROME to its path.')
  return found
}

// The DevTools protocol over the WebSocket Node has built in

class Page {
  private socket: WebSocket
  private next = 1
  private pending = new Map<number, { done: (value: any) => void; fail: (error: Error) => void }>()
  private listeners: ((method: string, params: any) => void)[] = []

  constructor(socket: WebSocket) {
    this.socket = socket
    socket.addEventListener('message', (message) => {
      const data = JSON.parse(String(message.data))
      if (data.id && this.pending.has(data.id)) {
        const waiting = this.pending.get(data.id)!
        this.pending.delete(data.id)
        if (data.error) waiting.fail(new Error(`${data.error.message}`))
        else waiting.done(data.result)
      } else if (data.method) for (const listener of this.listeners) listener(data.method, data.params)
    })
  }

  static async open(url: string): Promise<Page> {
    const socket = new WebSocket(url)
    await new Promise((done, fail) => {
      socket.addEventListener('open', done, { once: true })
      socket.addEventListener('error', fail, { once: true })
    })
    return new Page(socket)
  }

  send(method: string, params: Record<string, unknown> = {}): Promise<any> {
    const id = this.next++
    this.socket.send(JSON.stringify({ id, method, params }))
    return new Promise((done, fail) => this.pending.set(id, { done, fail }))
  }

  on(listener: (method: string, params: any) => void): void {
    this.listeners.push(listener)
  }

  /** Run an expression (a promise is awaited) in the page and return its value. */
  async eval<T = any>(expression: string): Promise<T> {
    const result = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
    if (result.exceptionDetails) throw new Error(`in the page: ${result.exceptionDetails.exception?.description ?? result.exceptionDetails.text}`)
    return result.result.value as T
  }

  close(): void {
    this.socket.close()
  }
}

let page!: Page
let base = ''

function loadEvent(): Promise<void> {
  return new Promise<void>((done) => page.on((method) => method === 'Page.loadEventFired' && done()))
}

async function goto(path: string): Promise<void> {
  const loaded = loadEvent()
  await page.send('Page.navigate', { url: base + path })
  await loaded
  await settled()
}

async function reload(): Promise<void> {
  const loaded = loadEvent()
  await page.send('Page.reload')
  await loaded
  await settled()
}

/** Until the app has its snapshot and the page is idle a moment. */
async function settled(): Promise<void> {
  await waitFor('the app to connect', `!!document.querySelector('header [data-test="wordmark"]')`, 30)
  await sleep(400)
}

async function waitFor(what: string, condition: string, seconds = 30): Promise<void> {
  await waitUntil(what, () => page.eval<boolean>(`Boolean(${condition})`), seconds, 200)
}

const KEYS: Record<string, { code: string; vk: number; key?: string }> = {
  O: { code: 'KeyO', vk: 79 },
  P: { code: 'KeyP', vk: 80 },
  R: { code: 'KeyR', vk: 82 },
  D: { code: 'KeyD', vk: 68 },
  F: { code: 'KeyF', vk: 70 },
  E: { code: 'KeyE', vk: 69 },
  '1': { code: 'Digit1', vk: 49, key: '!' },
  '2': { code: 'Digit2', vk: 50, key: '@' },
  '4': { code: 'Digit4', vk: 52, key: '$' },
  Enter: { code: 'Enter', vk: 13, key: 'Enter' },
}

/** A Shift shortcut as a person presses it. `raw` sends no character, so a text field gets nothing typed. */
async function shortcut(name: string, raw = false): Promise<void> {
  const k = KEYS[name]
  const key = k.key ?? name
  const text = name === 'Enter' ? '\r' : key
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', modifiers: 0, key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16 })
  await page.send('Input.dispatchKeyEvent', {
    type: raw ? 'rawKeyDown' : 'keyDown',
    modifiers: 8,
    key,
    code: k.code,
    windowsVirtualKeyCode: k.vk,
    ...(raw ? {} : { text, unmodifiedText: text }),
  })
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 8, key, code: k.code, windowsVirtualKeyCode: k.vk })
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 0, key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16 })
  await sleep(250)
}

async function press(key: 'Tab' | 'Escape'): Promise<void> {
  const vk = key === 'Tab' ? 9 : 27
  await page.send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key, code: key, windowsVirtualKeyCode: vk })
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key, code: key, windowsVirtualKeyCode: vk })
}

async function click(selector: string): Promise<void> {
  const found = await page.eval<boolean>(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el) return false; el.click(); return true })()`)
  if (!found) throw new Error(`nothing to click at ${selector}`)
  await sleep(300)
}

const text = (selector: string) => page.eval<string>(`document.querySelector(${JSON.stringify(selector)})?.textContent?.replace(/\\s+/g, ' ').trim() ?? ''`)
const path = () => page.eval<string>('location.pathname + location.search')
const api = <T = any>(url: string, init: Record<string, unknown> = {}) => page.eval<T>(`fetch(${JSON.stringify(url)}, ${JSON.stringify(init)}).then((r) => r.json())`)

async function screenshot(name: string): Promise<void> {
  const metrics = await page.send('Page.getLayoutMetrics')
  const height = Math.min(Math.ceil(metrics.cssContentSize.height), 8000)
  const shot = await page.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: 0, y: 0, width: 1600, height, scale: 1 } })
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(shot.data, 'base64'))
}

async function bothThemes(name: string): Promise<void> {
  const theme = await page.eval<string>('document.documentElement.dataset.theme')
  await screenshot(`${name}-${theme}`)
  await shortcut('D')
  await sleep(600)
  await screenshot(`${name}-${theme === 'dark' ? 'light' : 'dark'}`)
  await shortcut('D')
  await sleep(400)
}

/**
 * Tab from the top of the page until focus comes round again. Every control that should take focus
 * (visible, enabled or aria-disabled) must be reached, and each must show a ring when it has keyboard
 * focus: an outline or a box shadow (NFR-6).
 */
async function keyboard(id: string, where: string): Promise<void> {
  await page.eval(`(document.activeElement && document.activeElement.blur(), window.scrollTo(0, 0), window.__tabbed = [], window.__unringed = [], true)`)
  await page.eval(`(() => {
    if (window.__tabWatch) return true
    window.__tabWatch = true
    document.addEventListener('focusin', (event) => {
      const el = event.target
      const style = getComputedStyle(el)
      const ring = (style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0) || style.boxShadow !== 'none'
      window.__tabbed.push(el)
      if (!ring && el.matches(':focus-visible')) window.__unringed.push(el.outerHTML.slice(0, 90))
    })
    return true
  })()`)
  // Start where a person starts: a click on the top bar's empty middle puts the starting point at the
  // top of the page. Tab then walks forward until focus leaves the document or comes round again.
  await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 3, y: 3, button: 'left', clickCount: 1 })
  await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 3, y: 3, button: 'left', clickCount: 1 })
  await page.eval(`(window.__tabbed = [], window.__unringed = [], true)`)
  const limit = await page.eval<number>(`document.querySelectorAll('a[href], button, input, textarea, select, [tabindex]').length + 5`)
  for (let i = 0; i < limit; i++) {
    await press('Tab')
    const done = await page.eval<boolean>(`(() => {
      const active = document.activeElement
      if (!active || active === document.body) return window.__tabbed.length > 0
      return window.__tabbed.indexOf(active) !== window.__tabbed.length - 1
    })()`)
    if (done) break
  }
  await sleep(100)
  const result = await page.eval<{ missed: string[]; unringed: string[]; reached: number }>(`(() => {
    const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden' }
    const wanted = [...document.querySelectorAll('a[href], button, input, textarea, select, [tabindex]:not([tabindex="-1"])')]
      .filter((el) => !el.disabled && el.getAttribute('tabindex') !== '-1' && !el.closest('[inert], [hidden]') && visible(el))
      .filter((el) => !el.closest('[role="tablist"]') || el.getAttribute('aria-selected') === 'true')
    const reached = new Set(window.__tabbed)
    return {
      reached: reached.size,
      missed: wanted.filter((el) => !reached.has(el)).map((el) => el.outerHTML.slice(0, 90)),
      unringed: [...new Set(window.__unringed)],
    }
  })()`)
  check(id, `${where}: Tab reaches every control, each with a visible focus ring`, !result.missed.length && !result.unringed.length, `${result.reached} reached${result.missed.length ? `; missed ${result.missed.join(' | ')}` : ''}${result.unringed.length ? `; no ring on ${result.unringed.join(' | ')}` : ''}`)
}

/** From View Dashboard to every panel drawn, in the page's own clock (NFR-3). The waiting treemap of
 * iteration 1 (L-1) is the planted exception and is reported, not counted. */
async function dashboardRender(): Promise<{ ms: number; waiting: string[] }> {
  return page.eval(`new Promise((done) => {
    const start = performance.now()
    document.querySelector('[data-test="report-actions"] [data-action="dashboard"]').click()
    const drawn = (panel) => {
      if (panel.matches('[data-test="kpi"]')) return !!panel.querySelector('[data-test="kpi-figure"]')?.textContent.trim()
      if (panel.matches('[data-test="table-panel"]')) return panel.querySelectorAll('[data-test="row"]').length > 0
      return !!panel.querySelector('[data-test="chart-canvas"] canvas') || !!panel.querySelector('[data-test="chart-waiting"]')
    }
    const tick = () => {
      const root = document.querySelector('[data-test="dashboard"]')
      const panels = root ? [...root.querySelectorAll('[data-panel]')] : []
      if (root && root.getAttribute('aria-busy') === 'false' && panels.length && panels.every(drawn)) {
        const waiting = panels.filter((p) => p.querySelector('[data-test="chart-waiting"]')).map((p) => p.dataset.panel)
        requestAnimationFrame(() => done({ ms: Math.round(performance.now() - start), waiting }))
      } else requestAnimationFrame(tick)
    }
    tick()
  })`)
}

async function waitForReport(iteration: number, seconds: number): Promise<number> {
  const started = Date.now()
  await waitFor(`iteration ${iteration}'s report`, `document.querySelector('[data-test="report-verdict"]')`, seconds)
  return (Date.now() - started) / 1000
}

// The rehearsal

async function rehearse(): Promise<void> {
  apiPort = await freePort()
  const appPort = await freePort()
  base = `http://127.0.0.1:${appPort}`
  await startBackend()
  start(process.execPath, [join(FRONTEND, 'node_modules', 'vite', 'bin', 'vite.js'), '--port', String(appPort), '--strictPort'], FRONTEND, {
    SEEDFOUNDRY_API_URL: `http://127.0.0.1:${apiPort}`,
  })
  await waitUntil('Vite', () => answers(base + '/'), 60)

  const profile = join(WORK, 'chrome')
  start(findChrome(), [
    '--headless=new',
    '--remote-debugging-port=0',
    `--user-data-dir=${profile}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--disable-background-networking',
    '--disable-component-update',
    '--disable-sync',
    '--window-size=1600,1000',
    // Offline: no host resolves but this machine's loopback.
    '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',
    'about:blank',
  ], ROOT, {})
  const devtools = await waitUntil('Chrome', async () => (existsSync(join(profile, 'DevToolsActivePort')) ? readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0] : null), 30)
  const targets = await waitUntil('a page', async () => ((await (await fetch(`http://127.0.0.1:${devtools}/json/list`)).json()) as any[]).find((t) => t.type === 'page'), 10)
  page = await Page.open(targets.webSocketDebuggerUrl)

  const requests: string[] = []
  page.on((method, params) => {
    if (method === 'Network.requestWillBeSent') requests.push(params.request.url)
    if (method === 'Network.webSocketCreated') requests.push(params.url)
  })
  await page.send('Page.enable')
  await page.send('Runtime.enable')
  await page.send('Network.enable')
  await page.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false })
  // Long tasks, kept from the first script on every page load.
  await page.send('Page.addScriptToEvaluateOnNewDocument', {
    source: `window.__longtasks = []; try { new PerformanceObserver((list) => { for (const e of list.getEntries()) window.__longtasks.push({ at: e.startTime, ms: e.duration }) }).observe({ type: 'longtask', buffered: true }) } catch {}`,
  })

  // Knowledge, empty (AC-6, AC-10)
  await goto('/knowledge')
  check('AC-6', 'Start Build is disabled until the four core files exist, and says what is missing', (await page.eval(`document.querySelector('[data-test="start-build"]').getAttribute('aria-disabled') === 'true'`)) && (await page.eval<string>(`document.body.textContent`)).includes('Missing: Person, Instrument Awareness, Environment, Music'))
  await shortcut('O')
  const shown = await page.eval<boolean>(`!!document.querySelector('[data-test="demo-panel"]')`)
  await shortcut('O')
  const hidden = await page.eval<boolean>(`!document.querySelector('[data-test="demo-panel"]')`)
  check('AC-10', 'Shift+O shows and hides the demo controller', shown && hidden)
  if (SPEED !== 1) await shortcut(String(SPEED))
  await shortcut('P')
  await waitFor('the sample files', `document.querySelectorAll('[data-test="file-panel"] button.file').length === 5`, 15)
  check('AC-10', 'Shift+P loads the sample Seed', true, '5 files')
  const sample = await api<any[]>('/api/intake/files').then((files) => files.map((f) => [f.name, f.category, f.content]))
  // A shortcut in a text field does nothing (AC-10): Shift+O with the caret in the editor.
  await page.eval(`document.querySelector('[data-test="text"]').focus()`)
  await shortcut('O', true)
  check('AC-10', 'A shortcut in the editor does nothing', await page.eval<boolean>(`!document.querySelector('[data-test="demo-panel"]')`))
  check('AC-6', 'With the four core files, Start Build is enabled', await page.eval<boolean>(`document.querySelector('[data-test="start-build"]').getAttribute('aria-disabled') !== 'true' && !document.querySelector('[data-test="start-build"]').disabled`))
  await keyboard('NFR-6', 'Knowledge')
  await bothThemes('01-knowledge')

  // Iteration 1 (AC-1, AC-7)
  await page.eval(`document.activeElement?.blur(), true`)
  const t1 = Date.now()
  await shortcut('Enter')
  await waitFor('the Build page', `location.pathname === '/build/1'`, 10)
  check('AC-10', 'Shift+Enter starts the build and opens its page', true)
  // A reload partway through resumes with the full log (AC-7).
  await sleep(30_000 / SPEED)
  await reload()
  await waitFor('the console', `document.querySelectorAll('[data-test="console-line"]').length > 0`, 15)
  await sleep(300)
  const resumed = await page.eval<{ shown: number; kept: number }>(`(async () => {
    const shown = document.querySelectorAll('[data-test="console-line"]').length
    const r = await fetch('/api/builds/b-1/events').then((r) => r.json())
    const kept = r.events.filter((e) => !['step.started', 'step.completed'].includes(e.type)).length
    return { shown, kept }
  })()`)
  check('AC-7', 'A reload mid-build shows the full log so far', resumed.shown > 0 && Math.abs(resumed.shown - resumed.kept) <= 3, `${resumed.shown} console lines, ${resumed.kept} events held`)
  const longFrom = await page.eval<number>('performance.now()')
  const first = await waitForReport(1, 150 / SPEED)
  const took1 = (Date.now() - t1) / 1000
  timings['iteration 1 build (s)'] = Math.round(took1 * 10) / 10
  const longtasks = await page.eval<{ at: number; ms: number }[]>(`window.__longtasks.filter((t) => t.at > ${longFrom})`)
  const worst = Math.round(Math.max(0, ...longtasks.map((t) => t.ms)))
  timings['longest task while the console streamed (ms)'] = worst
  check('NFR-3', 'The console streams a whole build without jank (no task over 200 ms)', worst <= 200, `${longtasks.length} long tasks, the longest ${worst} ms`)
  const expected = 75 / SPEED
  check('AC-1', `Iteration 1 completes in ${SPEED === 1 ? '60 to 90 s at 1x' : `about ${expected} s at ${SPEED}x`}`, took1 >= 60 / SPEED - 2 && took1 <= 90 / SPEED + 3, `${took1.toFixed(1)} s by the wall clock (${first.toFixed(1)} s after the reload)`)
  await waitFor('the console to end', `[...document.querySelectorAll('[data-test="console-line"]')].some((l) => l.textContent.includes('Build completed'))`, 10)
  const lines1 = await page.eval<number>(`document.querySelectorAll('[data-test="console-line"]').length`)
  const ids1 = await page.eval<string[]>(`[...document.querySelectorAll('[data-test="finding"]')].map((r) => r.dataset.finding)`)
  check('AC-1', 'Iteration 1 finds exactly the 14 catalogued defects', JSON.stringify(ids1) === JSON.stringify(CATALOGUE), `${ids1.join(', ')}; ${lines1} console lines`)
  const rowsWithValues = await page.eval<boolean>(`[...document.querySelectorAll('[data-test="finding"]')].every((r) => r.querySelector('[data-test="finding-expected"]').textContent.trim() && r.querySelector('[data-test="finding-shown"]').textContent.trim())`)
  check('AC-2', 'The report lists each finding with expected and shown', rowsWithValues)
  await keyboard('NFR-6', 'Build page with the report')
  await bothThemes('02-build-1-report')

  // The iteration 1 dashboard (NFR-3, AC-2)
  const render1 = await dashboardRender()
  timings['iteration 1 dashboard first render (ms)'] = render1.ms
  check('NFR-3', 'Iteration 1 dashboard renders in under 1 s, the slow panel aside', render1.ms < 1000 && JSON.stringify(render1.waiting) === '["seats-treemap"]', `${render1.ms} ms; waiting: ${render1.waiting.join(', ') || 'none'}`)
  await waitFor('the slow treemap', `!document.querySelector('[data-test="chart-waiting"]')`, 10)
  check('AC-2', 'The slow panel draws after its wait (L-1)', true)
  await keyboard('NFR-6', 'Iteration 1 dashboard')
  await bothThemes('03-dashboard-1')
  await click('[data-test="back-to-report"]')

  // Reject with Prefill (AC-3, D-81)
  await click('[data-test="report-actions"] [data-action="rebuild"]')
  await waitFor('the rebuild modal', `document.querySelector('[role="dialog"][data-modal="rebuild"]')`, 5)
  await shortcut('F')
  await waitFor('the prefilled feedback', `document.querySelector('[role="dialog"] textarea')?.value.includes('N-1 to N-5')`, 5)
  check('AC-10', 'Shift+F prefills the rebuild feedback', true)
  await screenshot('04-rebuild-modal')
  const t2 = Date.now()
  await click('[data-action="start-rebuild"]')
  await waitFor('the iteration 2 Build page', `location.pathname === '/build/2'`, 10)
  await waitForReport(2, 150 / SPEED)
  const took2 = (Date.now() - t2) / 1000
  timings['iteration 2 build (s)'] = Math.round(took2 * 10) / 10
  check('AC-3', 'Iteration 2 completes with zero findings, verdict Passed', (await text('[data-test="report-verdict"]')) === 'Passed' && (await page.eval<number>(`document.querySelectorAll('[data-test="finding"]').length`)) === 0, `${took2.toFixed(1)} s`)
  check('AC-3', 'The report shows all 14 iteration 1 findings resolved and quotes the feedback', (await text('[data-test="changes-summary"]')) === '14 of 14 iteration 1 findings resolved.' && !!(await text('[data-test="changes-feedback"]')))
  // The stakeholder's feedback after M13 (D-80 to D-83): no iteration total, Reject on a passed
  // iteration 2, the context footprint within its budget, and the feedback shown going into the files.
  const feedbackLook = await page.eval<{ badge: string; reject: string | null; context: string; files: number }>(`({
    badge: document.querySelector('[data-test="iteration-badge"]')?.textContent.trim() ?? '',
    reject: (() => { const b = document.querySelector('[data-test="report-actions"] [data-action="rebuild"]'); return b ? b.getAttribute('aria-disabled') : 'absent' })(),
    context: document.querySelector('[data-test="context-verdict"]')?.textContent.trim() ?? '',
    files: [...document.querySelectorAll('[data-test="routing-file"] [data-test="routing-state"]')].filter((c) => c.textContent.trim() === 'Updated').length,
  })`)
  check(
    'D-81',
    'Iteration 2 reads "Iteration 2", offers Reject, shows the context footprint within budget and the feedback in all four files',
    feedbackLook.badge === 'Iteration 2' && feedbackLook.reject === null && feedbackLook.context === 'Within budget' && feedbackLook.files === 4,
    JSON.stringify(feedbackLook),
  )
  await bothThemes('05-build-2-report')
  const render2 = await dashboardRender()
  timings['iteration 2 dashboard first render (ms)'] = render2.ms
  check('NFR-3', 'Iteration 2 dashboard renders in under 1 s', render2.ms < 1000 && !render2.waiting.length, `${render2.ms} ms`)
  await sleep(800)
  await bothThemes('06-dashboard-2')
  await click('[data-test="back-to-report"]')

  // Approve and the Seed page (AC-4)
  await click('[data-test="report-actions"] [data-action="approve"]')
  await waitFor('the Seed page', `location.pathname === '/seed' && document.querySelector('[data-test="seed-name"]')`, 10)
  const sections = await page.eval<string[]>(`[...document.querySelectorAll('[data-test="seed"] h2')].map((h) => h.textContent.trim())`)
  check('AC-4', 'Approve on iteration 2 opens the Seed page with every section', JSON.stringify(sections) === JSON.stringify(['What this Seed does', 'Tests conducted', 'Iteration history', 'Seed files']), sections.join(', '))
  const downloads = await page.eval<{ name: string; bytes: number; dash: boolean; status: number }[]>(`Promise.all([...document.querySelectorAll('[data-test="seed"] a[download]')].map(async (a) => {
    const r = await fetch(a.getAttribute('href'))
    const body = new Uint8Array(await r.arrayBuffer())
    return { name: a.getAttribute('download'), bytes: body.length, dash: new TextDecoder().decode(body).includes(${JSON.stringify(EM_DASH)}), status: r.status }
  }))`)
  check('AC-4', 'The three files and the zip download, with no em dash', downloads.length === 4 && downloads.every((d) => d.status === 200 && d.bytes > 0 && !d.dash), downloads.map((d) => `${d.name} ${d.bytes} B`).join(', '))
  await click('[data-test="feedback-toggle"]')
  await keyboard('NFR-6', 'Seed page')
  await bothThemes('07-seed-iteration-2')
  await click('[data-file="core.md"] [data-action="preview"]')
  await sleep(400)
  await screenshot('08-seed-preview')
  await press('Escape')

  // A 1 MB file in the editor (NFR-3). Knowledge is still editable after approval.
  const big = await api(`/api/intake/files`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'large-notes.md', category: 'misc_context', content: '# Large notes\n\n' + NOTE.repeat(Math.floor(1_000_000 / NOTE.length)) }),
  })
  await goto(`/knowledge?file=${big.id}`)
  await waitFor('the 1 MB file', `document.querySelector('[data-test="text"]')?.value.length > 900000`, 15)
  await page.eval(`(() => {
    const area = document.querySelector('[data-test="text"]')
    area.focus(); area.setSelectionRange(area.value.length, area.value.length)
    // Each key from its own timestamp (when the key arrived) to the next frame, so every handler it
    // runs, the app's included, falls inside the measure.
    window.__keys = []
    window.addEventListener('keydown', (e) => { const start = e.timeStamp; requestAnimationFrame(() => window.__keys.push(performance.now() - start)) }, true)
    window.__inputs = 0
    area.addEventListener('input', () => window.__inputs++)
    return true
  })()`)
  for (const char of 'typed into a 1 MB file') {
    const code = /[a-z]/.test(char) ? `Key${char.toUpperCase()}` : char === ' ' ? 'Space' : 'Digit1'
    const vk = char === ' ' ? 32 : char.toUpperCase().charCodeAt(0)
    await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: char, code, text: char, unmodifiedText: char, windowsVirtualKeyCode: vk })
    await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: char, code, windowsVirtualKeyCode: vk })
    await sleep(40)
  }
  await sleep(500)
  const typed = await page.eval<{ inputs: number; keys: number[] }>('({ inputs: window.__inputs, keys: window.__keys })')
  const slowest = Math.round(Math.max(0, ...typed.keys))
  timings['slowest keystroke in a 1 MB file (ms)'] = slowest
  check('NFR-3', 'The editor stays responsive with a 1 MB file (each keystroke drawn within 100 ms)', typed.inputs >= 20 && typed.keys.length >= 20 && slowest < 100, `${typed.inputs} keystrokes, the slowest ${slowest} ms to its frame; size ${big.size} bytes`)
  await sleep(1500) // autosave
  await api(`/api/intake/files/${big.id}`, { method: 'DELETE' }).catch(() => undefined)

  // A server restart keeps intake (AC-7) and the approved Seed.
  const before = await api<any[]>('/api/intake/files')
  const zipBefore = await page.eval<string>(`fetch('/api/seed/zip').then((r) => r.arrayBuffer()).then((b) => crypto.subtle.digest('SHA-256', b)).then((d) => [...new Uint8Array(d)].map((x) => x.toString(16).padStart(2, '0')).join(''))`)
  stop(backend)
  await sleep(1500)
  await startBackend()
  await goto('/seed')
  const after = await api<any[]>('/api/intake/files')
  const zipAfter = await page.eval<string>(`fetch('/api/seed/zip').then((r) => r.arrayBuffer()).then((b) => crypto.subtle.digest('SHA-256', b)).then((d) => [...new Uint8Array(d)].map((x) => x.toString(16).padStart(2, '0')).join(''))`)
  check('AC-7', 'A server restart keeps intake, and the Seed downloads the same zip', JSON.stringify(after) === JSON.stringify(before) && zipAfter === zipBefore, `${after.length} files; zip ${zipAfter.slice(0, 12)}`)

  // Reset, then approve iteration 1 instead (AC-5)
  await shortcut('R')
  await waitFor('the Reset question', `document.querySelector('[data-test="demo-confirm"]')`, 5)
  await click('[data-test="confirm-ok"]')
  await waitFor('Knowledge after Reset', `location.pathname === '/knowledge'`, 10)
  const reset = await api('/api/state')
  check('AC-10', 'Shift+R resets to start, the approval included', reset.builds.length === 0 && reset.approval === null && reset.intake.files.length === 0)
  await shortcut('P')
  await waitFor('the sample files', `document.querySelectorAll('[data-test="file-panel"] button.file').length === 5`, 15)
  const again = await api<any[]>('/api/intake/files').then((files) => files.map((f) => [f.name, f.category, f.content]))
  const differs = again.filter((f, n) => JSON.stringify(f) !== JSON.stringify(sample[n])).map((f) => f[0])
  check('NFR-1', 'Reset then Load sample gives the same Knowledge, byte for byte', again.length === sample.length && !differs.length, differs.length ? `differs: ${differs.join(', ')}` : `${again.length} files`)
  await page.eval(`document.activeElement?.blur(), true`)
  if (SPEED === 1) await shortcut('4') // the second path is not timed
  await shortcut('Enter')
  await waitFor('the Build page', `location.pathname === '/build/1'`, 10)
  await waitForReport(1, 150)
  await click('[data-test="report-actions"] [data-action="approve"]')
  await waitFor('the Seed page', `location.pathname === '/seed' && document.querySelector('[data-test="known-issue"]')`, 10)
  const issues = await page.eval<string[]>(`[...document.querySelectorAll('[data-test="known-issue"]')].map((r) => r.dataset.issue)`)
  const filesHaveIssues = await page.eval<boolean>(`Promise.all(['core.md', 'adaptation.md', 'protection.md'].map((n) => fetch('/api/seed/files/' + n).then((r) => r.text()))).then((texts) => texts.every((t) => ${JSON.stringify(CATALOGUE)}.every((id) => t.includes('- **' + id + '**'))))`)
  check('AC-5', 'Approve on iteration 1 lists every open finding on the page and in each file', JSON.stringify(issues) === JSON.stringify(CATALOGUE) && filesHaveIssues, `${issues.length} known issues`)
  await bothThemes('09-seed-iteration-1')
  if (SPEED === 1) await shortcut('1')

  // Nothing left this machine (AC-9)
  const outside = requests.filter((url) => !/^(https?|wss?):\/\/127\.0\.0\.1:\d+\//.test(url) && !/^(data|blob):/.test(url))
  check('AC-9', 'Chrome made no request outside 127.0.0.1, with every other host unresolvable', !outside.length, `${requests.length} requests${outside.length ? `; outside: ${outside.slice(0, 5).join(', ')}` : ''}`)
  const refused = existsSync(OFFLINE_LOG) ? readFileSync(OFFLINE_LOG, 'utf8').trim() : ''
  check('AC-9', 'The backend, under the offline guard, tried no lookup or connection outside loopback', !refused, refused || 'none')
}

let failed = false
try {
  await rehearse()
} catch (error) {
  failed = true
  console.error(`\nThe rehearsal stopped: ${(error as Error).message}`)
  try {
    if (page) await screenshot('stopped-here')
  } catch {
    // Chrome may be gone.
  }
} finally {
  page?.close()
  for (const child of children.reverse()) stop(child)
}

const passed = checks.filter((c) => c.pass).length
writeFileSync(join(OUT, 'results.json'), JSON.stringify({ speed: SPEED, checks, timings }, null, 1) + '\n')
console.log(`\n${passed} of ${checks.length} checks passed at ${SPEED}x.`)
for (const [name, value] of Object.entries(timings)) console.log(`  ${name}: ${value}`)
console.log(`Screenshots and results.json: ${OUT}`)
if (!process.argv.includes('--keep')) {
  try {
    rmSync(join(WORK, 'chrome'), { recursive: true, force: true })
    rmSync(VAR, { recursive: true, force: true })
  } catch {
    // Chrome can hold its profile a moment longer; the temp folder is the system's to clear.
  }
}
process.exit(failed || passed !== checks.length ? 1 : 0)
