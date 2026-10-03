// No network requests outside localhost (NFR-2, D-38). Finds every URL that names another
// host, in source or in the built bundle. Runs as `postbuild` over dist/, so `npm run build`
// fails on a violation; tests/network.spec.ts runs the same rules over src/.
//
//   node scripts/check-network.ts [dir]      (default: dist)
//
// Plain erasable TypeScript, so Node runs it without a build step.

import { readdirSync, readFileSync, statSync } from 'node:fs'
import { extname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const LOCAL_HOSTS = new Set(['127.0.0.1', 'localhost'])

/** Strings that look like URLs but are never fetched, allowed by name. */
export const NEVER_FETCHED = [
  { prefix: 'http://www.w3.org/', why: 'XML namespaces (SVG, XLink, MathML)' },
  { prefix: 'https://www.w3.org/', why: 'XML namespaces' },
  { prefix: 'https://vuejs.org/error-reference', why: "Vue's error-reference link, printed in error messages" },
]

// Any absolute URL with a scheme the page could fetch or connect to.
const ABSOLUTE = /\b(?:https?|wss?):\/\/[^\s"'`)<>\\]+/gi

// A protocol-relative URL (//host/...) where the page would fetch it: src, href, url(),
// @import, fetch(), import(), EventSource(), or an ES import.
const PROTOCOL_RELATIVE =
  /(?:\b(?:src|href|srcset|action|poster|data)\s*=\s*["']?|url\(\s*["']?|@import\s+["']?|\b(?:fetch|import|EventSource|WebSocket)\(\s*["'`]|\bfrom\s*["'])(\/\/[^\s"'`)<>\\]+)/gi

const TEXT_EXTENSIONS = new Set(['.html', '.js', '.mjs', '.cjs', '.css', '.json', '.svg', '.webmanifest', '.txt', '.map', '.ts', '.vue'])

export interface Violation {
  file: string
  line: number
  url: string
}

function hostOf(url: string): string {
  const rest = url.replace(/^(?:[a-z]+:)?\/\//i, '')
  return rest.split(/[/?#]/, 1)[0].replace(/:\d+$/, '').toLowerCase()
}

export function isAllowed(url: string): boolean {
  if (LOCAL_HOSTS.has(hostOf(url))) return true
  return NEVER_FETCHED.some((entry) => url.startsWith(entry.prefix))
}

/** URLs in the text that name a host other than this machine and are not allowed by name. */
export function findExternalUrls(text: string): { url: string; index: number }[] {
  const found: { url: string; index: number }[] = []
  for (const match of text.matchAll(ABSOLUTE)) {
    if (!isAllowed(match[0])) found.push({ url: match[0], index: match.index ?? 0 })
  }
  for (const match of text.matchAll(PROTOCOL_RELATIVE)) {
    const url = match[1]
    if (!isAllowed(url)) found.push({ url, index: (match.index ?? 0) + match[0].length - url.length })
  }
  return found.sort((a, b) => a.index - b.index)
}

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    return statSync(path).isDirectory() ? walk(path) : [path]
  })
}

/** Every violation in the text files under the given paths (files or directories). */
export function scan(paths: string[], root: string = process.cwd()): Violation[] {
  const files = paths.flatMap((path) => (statSync(path).isDirectory() ? walk(path) : [path]))
  const violations: Violation[] = []
  for (const file of files) {
    if (!TEXT_EXTENSIONS.has(extname(file))) continue
    const text = readFileSync(file, 'utf8')
    for (const { url, index } of findExternalUrls(text)) {
      const line = text.slice(0, index).split('\n').length
      violations.push({ file: relative(root, file).replaceAll('\\', '/'), line, url })
    }
  }
  return violations
}

function main(): void {
  const dir = resolve(process.argv[2] ?? 'dist')
  const violations = scan([dir])
  if (violations.length) {
    console.error(`Network check failed: ${violations.length} external URL(s) in ${relative(process.cwd(), dir) || dir}`)
    for (const v of violations) console.error(`  ${v.file}:${v.line}: ${v.url}`)
    process.exit(1)
  }
  console.log(`Network check passed: no external URL in ${relative(process.cwd(), dir) || dir}`)
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main()
