<script setup lang="ts">
// A modal dialog (NFR-6): focus moves into it on open and is trapped there, Escape closes it,
// and focus returns to the control that opened it. A click on the backdrop does not close it,
// so text being written in a modal is not lost by a stray click. `name` marks the dialog
// (`data-modal`) so the demo shortcuts that belong to it still work inside it (D-47); the
// `controls` slot sits in the header beside the title; `flush` leaves the body's padding and
// scrolling to the content, for panes that scroll on their own (the rebuild modal, D-70).
import { nextTick, onBeforeUnmount, ref, useId, watch } from 'vue'

const props = withDefaults(defineProps<{ open: boolean; title: string; size?: 'md' | 'lg'; name?: string; flush?: boolean }>(), {
  size: 'md',
  name: undefined,
  flush: false,
})
const emit = defineEmits<{ close: [] }>()

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[contenteditable="true"]',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

const titleId = useId()
const dialog = ref<HTMLElement | null>(null)
let opener: HTMLElement | null = null

function focusables(): HTMLElement[] {
  // A control taken out of the tab order (a tablist's other tabs) is not a stop for Tab.
  return dialog.value ? Array.from(dialog.value.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((el) => el.getAttribute('tabindex') !== '-1') : []
}

function restoreFocus(): void {
  const target = opener
  opener = null
  if (target && target.isConnected) target.focus()
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
      await nextTick()
      ;(focusables()[0] ?? dialog.value)?.focus()
    } else {
      restoreFocus()
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (props.open) restoreFocus()
})

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.stopPropagation()
    emit('close')
    return
  }
  if (event.key !== 'Tab') return
  const items = focusables()
  if (!items.length) {
    event.preventDefault()
    return
  }
  const first = items[0]
  const last = items[items.length - 1]
  const active = document.activeElement
  if (event.shiftKey && (active === first || active === dialog.value)) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="backdrop">
      <div
        ref="dialog"
        class="modal"
        :class="`modal--${size}`"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        :data-modal="name"
        tabindex="-1"
        @keydown="onKeydown"
      >
        <header class="modal__header">
          <h2 :id="titleId" class="modal__title">{{ title }}</h2>
          <div v-if="$slots.controls" class="modal__controls"><slot name="controls" /></div>
          <button type="button" class="modal__close" aria-label="Close" @click="emit('close')">
            <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
            </svg>
          </button>
        </header>
        <div class="modal__body" :class="{ 'modal__body--flush': flush }"><slot /></div>
        <footer v-if="$slots.footer" class="modal__footer"><slot name="footer" /></footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: var(--space-6);
  background: var(--backdrop);
}

.modal {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  width: min(560px, 100%);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.modal--lg {
  width: 90vw;
  height: 90vh;
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.modal__title {
  font-size: var(--text-lg);
  font-weight: 600;
}

.modal__controls {
  margin-left: auto;
}

.modal__close {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.modal__close:hover {
  border-color: var(--border-default);
  color: var(--text-primary);
}

.modal__body {
  flex: 1;
  overflow: auto;
  padding: var(--space-4);
}

.modal__body--flush {
  display: flex;
  min-height: 0;
  overflow: hidden;
  padding: 0;
}

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border-subtle);
}
</style>
