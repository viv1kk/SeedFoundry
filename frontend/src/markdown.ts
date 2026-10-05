// Markdown Preview (FR-IN-4, R-7, NFR-2, D-40). Two layers:
//
// 1. markdown-it with raw HTML off, so any HTML in a file is shown as text. Images and links
//    never become <img src> or <a href>: an image shows as "Image" plus its alt text and
//    address, and a link shows its text in link style plus its address. Nothing in Preview
//    can fetch or navigate. The typographer is off, so "---" never becomes an em dash (NFR-8).
// 2. DOMPurify over the result, with an allowlist of the tags markdown-it emits here and
//    only `class` (md- names) and `start` as attributes, in case layer 1 ever lets through
//    something it should not.

import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: false, linkify: false, typographer: false, langPrefix: 'md-lang-' })
const escape = md.utils.escapeHtml

// Table alignment arrives as style="text-align:..."; style is not allowed, so use a class.
md.core.ruler.push('align_class', (state) => {
  for (const token of state.tokens) {
    const style = String(token.attrGet('style') ?? '')
    if (!style) continue
    const align = style.match(/text-align:\s*(left|center|right)/)?.[1]
    token.attrs = (token.attrs ?? []).filter(([name]) => name !== 'style')
    if (align) token.attrJoin('class', `md-align-${align}`)
  }
})

md.renderer.rules.image = (tokens, idx) => {
  const token = tokens[idx]
  const alt = token.children ? md.renderer.renderInlineAsText(token.children, md.options, {}) : token.content
  const src = String(token.attrGet('src') ?? '')
  const label = alt ? ` ${escape(alt)}` : ''
  return `<span class="md-image"><span class="md-image-label">Image</span>${label} <span class="md-address">${escape(src)}</span></span>`
}

md.renderer.rules.link_open = () => '<span class="md-link">'

md.renderer.rules.link_close = (tokens, idx) => {
  // The address follows the text, unless the text is the address (an autolink).
  let open = idx - 1
  while (open >= 0 && tokens[open].type !== 'link_open') open--
  const token = tokens[open]
  if (!token || token.markup === 'autolink') return '</span>'
  return `</span> <span class="md-address">(${escape(String(token.attrGet('href') ?? ''))})</span>`
}

const ALLOWED_TAGS = [
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'hr', 'blockquote',
  'ul', 'ol', 'li', 'pre', 'code', 'em', 'strong', 's',
  'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span',
]
const ALLOWED_ATTR = ['class', 'start']

let purifier: ReturnType<typeof DOMPurify> | null = null

function purify(): ReturnType<typeof DOMPurify> {
  if (purifier) return purifier
  purifier = DOMPurify(window)
  // Keep only SeedFactory's md- class names, so a file cannot borrow the app's classes.
  purifier.addHook('uponSanitizeAttribute', (_node, data) => {
    if (data.attrName !== 'class') return
    const kept = data.attrValue.split(/\s+/).filter((name) => /^md-[\w-]+$/.test(name))
    if (kept.length) data.attrValue = kept.join(' ')
    else data.keepAttr = false
  })
  return purifier
}

/** Layer 2 on its own: an HTML string reduced to the Preview allowlist. */
export function sanitize(html: string): string {
  return purify().sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    ALLOW_ARIA_ATTR: false,
    KEEP_CONTENT: true,
  })
}

/** Markdown to safe HTML for Preview. */
export function renderMarkdown(text: string): string {
  return sanitize(md.render(text))
}
