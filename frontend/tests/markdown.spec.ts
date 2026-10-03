// Preview (FR-IN-4) renders markdown, sanitised (R-7), and never fetches (NFR-2, D-40).

import { mount } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import MarkdownPreview from '../src/components/intake/MarkdownPreview.vue'
import { renderMarkdown, sanitize } from '../src/markdown'

const HOSTILE = readFileSync(resolve(__dirname, 'fixtures/hostile.md'), 'utf8')

const ALLOWED_TAGS = new Set([
  'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'BR', 'HR', 'BLOCKQUOTE', 'UL', 'OL', 'LI', 'PRE', 'CODE',
  'EM', 'STRONG', 'S', 'TABLE', 'THEAD', 'TBODY', 'TR', 'TH', 'TD', 'SPAN',
])

function fragment(html: string): HTMLElement {
  const root = document.createElement('div')
  root.innerHTML = html
  return root
}

/** Everything in rendered HTML that could run or fetch. */
function hazards(root: HTMLElement): string[] {
  const found: string[] = []
  for (const el of Array.from(root.querySelectorAll('*'))) {
    if (!ALLOWED_TAGS.has(el.tagName)) found.push(`<${el.tagName.toLowerCase()}>`)
    for (const attr of Array.from(el.attributes)) {
      if (attr.name !== 'class' && attr.name !== 'start') found.push(`${el.tagName.toLowerCase()}[${attr.name}]`)
      if (attr.name === 'class' && !attr.value.split(/\s+/).every((name) => /^md-[\w-]+$/.test(name))) {
        found.push(`class="${attr.value}"`)
      }
    }
  }
  return found
}

beforeEach(() => {
  delete (window as unknown as Record<string, unknown>).__hostile
})

afterEach(() => {
  vi.unstubAllGlobals()
  document.body.innerHTML = ''
})

describe('FR-IN-4: Preview renders markdown', () => {
  it('renders headings, lists, emphasis, code and blockquotes', () => {
    const root = fragment(
      renderMarkdown('# Title\n\n## Part\n\n- one\n- two\n\n1. first\n2. second\n\n*em* **strong** ~~gone~~ `code`\n\n```\nblock\n```\n\n> quoted'),
    )
    expect(root.querySelector('h1')?.textContent).toBe('Title')
    expect(root.querySelector('h2')?.textContent).toBe('Part')
    expect(Array.from(root.querySelectorAll('ul li')).map((li) => li.textContent)).toEqual(['one', 'two'])
    expect(root.querySelectorAll('ol li')).toHaveLength(2)
    expect(root.querySelector('em')?.textContent).toBe('em')
    expect(root.querySelector('strong')?.textContent).toBe('strong')
    expect(root.querySelector('s')?.textContent).toBe('gone')
    expect(root.querySelector('p code')?.textContent).toBe('code')
    expect(root.querySelector('pre code')?.textContent).toBe('block\n')
    expect(root.querySelector('blockquote')?.textContent?.trim()).toBe('quoted')
  })

  it('renders tables, with alignment as a class rather than a style', () => {
    const root = fragment(renderMarkdown('| Name | Seats |\n|:---|---:|\n| A | 12 |'))
    expect(Array.from(root.querySelectorAll('th')).map((th) => th.textContent)).toEqual(['Name', 'Seats'])
    expect(root.querySelector('td.md-align-right')?.textContent).toBe('12')
    expect(root.querySelector('[style]')).toBeNull()
  })

  it('keeps a numbered list start', () => {
    expect(fragment(renderMarkdown('3. three\n4. four')).querySelector('ol')?.getAttribute('start')).toBe('3')
  })

  it('shows a link as link-styled text and its address, without an href (D-40)', () => {
    const root = fragment(renderMarkdown('See [the notes](https://notes.example.com/a) and <https://example.com/b>.'))
    const links = root.querySelectorAll('.md-link')
    expect(Array.from(links).map((l) => l.textContent)).toEqual(['the notes', 'https://example.com/b'])
    expect(root.querySelector('.md-address')?.textContent).toBe('(https://notes.example.com/a)')
    expect(root.querySelectorAll('.md-address')).toHaveLength(1)
    expect(root.querySelector('a, [href]')).toBeNull()
  })

  it('shows an image as text: its label, alt text and address, never an img (D-40)', () => {
    const root = fragment(renderMarkdown('![A chart](https://images.example.com/chart.png)'))
    const image = root.querySelector('.md-image')
    expect(image?.textContent).toBe('Image A chart https://images.example.com/chart.png')
    expect(root.querySelector('img, [src]')).toBeNull()
  })

  it('never turns hyphens into an em dash (NFR-8)', () => {
    const html = renderMarkdown('one --- two -- three')
    expect(html).toContain('one --- two -- three')
    expect(html).not.toContain(String.fromCharCode(0x2014))
  })
})

describe('R-7: the hostile sample renders safely', () => {
  it('leaves nothing executable or fetchable in the output', () => {
    const html = renderMarkdown(HOSTILE)
    expect(hazards(fragment(html))).toEqual([])
    // The same over the string, inside real tags (escaped text shows "&lt;img src=", which is safe).
    expect(html).not.toMatch(/<[a-z][^>]*\s(?:src|href|srcset|srcdoc|poster|action|data|style|on\w+)\s*=/i)
    expect(html).not.toMatch(/<(script|iframe|img|svg|style|link|meta|base|object|embed|video|form|input|details|body|a)\b/i)
  })

  it('shows raw HTML as text instead of rendering it', () => {
    const root = fragment(renderMarkdown(HOSTILE))
    expect(root.textContent).toContain("<script>window.__hostile = 'script tag ran'</script>")
    expect(root.textContent).toContain('<iframe src="https://evil.example.com/frame"></iframe>')
  })

  it('does not make javascript:, vbscript: or data: targets into links', () => {
    const root = fragment(renderMarkdown(HOSTILE))
    const linked = Array.from(root.querySelectorAll('.md-link, .md-address')).map((el) => el.textContent ?? '')
    expect(linked.filter((text) => /javascript:|vbscript:|data:text/i.test(text))).toEqual([])
    expect(root.textContent).toContain("[javascript link](javascript:window.__hostile='md link ran')")
  })

  it('shows remote images as text and names their address', () => {
    const images = Array.from(fragment(renderMarkdown(HOSTILE)).querySelectorAll('.md-image'))
    expect(images.map((el) => el.querySelector('.md-address')?.textContent)).toEqual([
      'https://evil.example.com/pixel.png',
      '//evil.example.com/pixel.png',
      'data:image/png;base64,iVBORw0KGgo=',
      'https://evil.example.com/ref.png',
    ])
  })

  it('drops a code fence language that tries to break out of its class', () => {
    const root = fragment(renderMarkdown(HOSTILE))
    expect(Array.from(root.querySelectorAll('code')).every((el) => !el.hasAttribute('class'))).toBe(true)
  })

  it('the sanitiser alone also strips hostile HTML (second layer)', () => {
    const raw = [
      '<script>window.__hostile = 1</script>',
      '<img src="x" onerror="window.__hostile = 2">',
      '<svg onload="window.__hostile = 3"><script>window.__hostile = 4</script></svg>',
      '<iframe src="https://evil.example.com/"></iframe>',
      '<a href="javascript:alert(1)">link</a>',
      '<p style="background:url(https://evil.example.com/a.png)" class="backdrop md-ok">text</p>',
      '<style>@import "https://evil.example.com/x.css";</style>',
      '<math><mtext><table><mglyph><style><img src=x onerror=alert(1)>',
    ].join('')
    const root = fragment(sanitize(raw))
    expect(hazards(root)).toEqual([])
    expect(root.querySelector('p')?.getAttribute('class')).toBe('md-ok')
    expect(root.textContent).toContain('link')
  })
})

describe('NFR-2: Preview makes no network request', () => {
  it('mounting Preview of the hostile sample fetches nothing and runs nothing', async () => {
    const fetchSpy = vi.fn()
    const open = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const realOpen = XMLHttpRequest.prototype.open
    XMLHttpRequest.prototype.open = open
    const created: string[] = []
    const realCreate = document.createElement.bind(document)
    const createSpy = vi.spyOn(document, 'createElement').mockImplementation((tag: string, options?: ElementCreationOptions) => {
      created.push(tag.toLowerCase())
      return realCreate(tag, options)
    })
    try {
      const wrapper = mount(MarkdownPreview, { props: { text: HOSTILE, label: 'Preview of hostile.md' }, attachTo: document.body })
      await new Promise((r) => setTimeout(r, 20))
      const preview = wrapper.get('[data-test="preview"]').element as HTMLElement
      expect(hazards(preview)).toEqual([])
      expect(preview.querySelectorAll('img, iframe, script, link, object, embed, video, audio, source, svg')).toHaveLength(0)
      expect(fetchSpy).not.toHaveBeenCalled()
      expect(open).not.toHaveBeenCalled()
      expect(created.filter((tag) => ['img', 'iframe', 'script', 'link', 'image', 'audio', 'video'].includes(tag))).toEqual([])
      expect((window as unknown as Record<string, unknown>).__hostile).toBeUndefined()
      wrapper.unmount()
    } finally {
      XMLHttpRequest.prototype.open = realOpen
      createSpy.mockRestore()
    }
  })
})
