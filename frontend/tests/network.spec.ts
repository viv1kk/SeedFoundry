// No network requests outside localhost (NFR-2, D-38). The same rules run as `postbuild`
// over dist/, so `npm run build` fails on a violation.

import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { findExternalUrls, scan } from '../scripts/check-network'

const FRONTEND = resolve(__dirname, '..')

describe('source', () => {
  it('names no external URL in src/ or index.html', () => {
    expect(scan([resolve(FRONTEND, 'src'), resolve(FRONTEND, 'index.html')], FRONTEND)).toEqual([])
  })

  it('bundles the fonts from npm instead of fetching them', () => {
    expect(scan([resolve(FRONTEND, 'node_modules/@fontsource-variable/inter/index.css')], FRONTEND)).toEqual([])
    expect(scan([resolve(FRONTEND, 'node_modules/@fontsource-variable/jetbrains-mono/index.css')], FRONTEND)).toEqual([])
  })
})

describe('the checker', () => {
  const urls = (text: string) => findExternalUrls(text).map((f) => f.url)

  it.each([
    ['a script src', '<script src="https://cdn.example.com/vue.js"></script>', 'https://cdn.example.com/vue.js'],
    ['a stylesheet href', '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">', 'https://fonts.googleapis.com/css2?family=Inter'],
    ['a protocol-relative src', '<img src="//images.example.com/a.png">', '//images.example.com/a.png'],
    ['a CSS url()', '@font-face{src:url(https://fonts.gstatic.com/s/inter.woff2)}', 'https://fonts.gstatic.com/s/inter.woff2'],
    ['a protocol-relative url()', "a{background:url('//cdn.example.com/x.png')}", '//cdn.example.com/x.png'],
    ['an @import', '@import "//fonts.example.com/inter.css";', '//fonts.example.com/inter.css'],
    ['a fetch()', 'fetch("https://api.example.com/v1")', 'https://api.example.com/v1'],
    ['a websocket', 'new WebSocket("wss://events.example.com")', 'wss://events.example.com'],
    ['a dynamic import()', 'import("//cdn.example.com/mod.js")', '//cdn.example.com/mod.js'],
    ['a non-error vuejs.org page', 'see https://vuejs.org/guide/', 'https://vuejs.org/guide/'],
  ])('finds %s', (_, text, url) => {
    expect(urls(text)).toEqual([url])
  })

  it.each([
    ['localhost', 'fetch("http://localhost:5273/api/state")'],
    ['127.0.0.1 with a port', 'const BACKEND = "http://127.0.0.1:8100"'],
    ['a relative API path', 'fetch("/api/state")'],
    ['an XML namespace', 'createElementNS("http://www.w3.org/2000/svg","svg")'],
    ["Vue's error-reference link", '`https://vuejs.org/error-reference/#runtime-${r}`'],
    ['a JS comment', 'a = 1 // not a url'],
  ])('allows %s', (_, text) => {
    expect(urls(text)).toEqual([])
  })

  it('reports the file and line', () => {
    const found = findExternalUrls('ok\nok\n<script src="https://x.example.com/a.js">')
    expect(found).toHaveLength(1)
  })
})
