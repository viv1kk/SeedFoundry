// The demo controller's Shift shortcuts (seed-reuse-notes.md section 6.2, OQ-5) and when they
// are ignored (FR-DC-1, D-47). Letters match on KeyboardEvent.key, case-insensitive, so Caps
// Lock does not matter; digits match on KeyboardEvent.code, so Shift+1 works on any layout
// even though it types "!" on a US keyboard.

export type DemoAction =
  | 'toggle'
  | 'sample'
  | 'start'
  | 'speed1'
  | 'speed2'
  | 'speed4'
  | 'skipPhase'
  | 'skipEnd'
  | 'prefill'
  | 'clear'
  | 'reset'
  | 'theme'

export interface Shortcut {
  action: DemoAction
  /** As the panel and the operator guide show it. */
  label: string
  /** KeyboardEvent.key, lower case. */
  key?: string
  /** KeyboardEvent.code, for keys whose character depends on the layout. */
  code?: string
  /** The modal this shortcut belongs to: it fires only while that modal is open. */
  modal?: string
}

export const SHORTCUTS: readonly Shortcut[] = [
  { action: 'toggle', label: 'Shift+O', key: 'o' },
  { action: 'sample', label: 'Shift+P', key: 'p' },
  { action: 'start', label: 'Shift+Enter', key: 'enter' },
  { action: 'speed1', label: 'Shift+1', code: 'Digit1' },
  { action: 'speed2', label: 'Shift+2', code: 'Digit2' },
  { action: 'speed4', label: 'Shift+4', code: 'Digit4' },
  { action: 'skipPhase', label: 'Shift+S', key: 's' },
  { action: 'skipEnd', label: 'Shift+E', key: 'e' },
  // The rebuild modal (M10) marks itself data-modal="rebuild".
  { action: 'prefill', label: 'Shift+F', key: 'f', modal: 'rebuild' },
  { action: 'clear', label: 'Shift+C', key: 'c' },
  { action: 'reset', label: 'Shift+R', key: 'r' },
  { action: 'theme', label: 'Shift+D', key: 'd' },
]

export function shortcutOf(action: DemoAction): Shortcut {
  return SHORTCUTS.find((s) => s.action === action)!
}

/** The shortcut a key press asks for, before any focus or modal rule. Shift alone, no repeats. */
export function matchShortcut(event: KeyboardEvent): Shortcut | null {
  if (!event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) return null
  if (event.repeat || event.isComposing || event.defaultPrevented) return null
  const key = event.key.toLowerCase()
  return SHORTCUTS.find((s) => (s.code ? event.code === s.code : key === s.key)) ?? null
}

// Anywhere text is typed: a capital letter typed there is text, never a shortcut. The
// Knowledge editor is a textarea and its name field an input (D-41); data-no-shortcuts is
// for any later editing surface that is neither.
const TYPING = 'input, textarea, select, [contenteditable]:not([contenteditable="false"]), [data-no-shortcuts]'

export function takesTyping(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest(TYPING) !== null
}

// Enter already activates a focused button or link, so Shift+Enter there is that control's.
const ACTIVATES_ON_ENTER = 'button, a[href], summary, [role="button"], [role="menuitem"], [role="option"], [role="tab"]'

export function activatesOnEnter(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest(ACTIVATES_ON_ENTER) !== null
}

/** The open modal's data-modal name ('' when it has none), or null when no modal is open. */
export function openModal(): string | null {
  const dialog = document.querySelector('[role="dialog"][aria-modal="true"]')
  return dialog ? (dialog.getAttribute('data-modal') ?? '') : null
}

/** The action a key press should run, after the focus and modal rules (FR-DC-1). */
export function shortcutAction(event: KeyboardEvent): DemoAction | null {
  const shortcut = matchShortcut(event)
  if (!shortcut || takesTyping(event.target)) return null
  const modal = openModal()
  if (shortcut.modal ? modal !== shortcut.modal : modal !== null) return null
  if (shortcut.action === 'start' && activatesOnEnter(event.target)) return null
  return shortcut.action
}
