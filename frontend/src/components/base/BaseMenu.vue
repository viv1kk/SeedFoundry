<script setup lang="ts">
// A menu button (NFR-6), following the WAI-ARIA menu button pattern: Enter, Space or the
// arrow keys open it on an item; arrows, Home and End move; Enter or Space picks; Escape
// closes and focus goes back to the button; Tab closes and moves on; a click outside closes.
// Items with `checked` are radio items, for picking one of several (the category picker).
import { computed, nextTick, onBeforeUnmount, ref, useId } from 'vue'

export interface MenuItem {
  id: string
  label: string
  checked?: boolean
  disabled?: boolean
}

const props = withDefaults(
  defineProps<{ items: MenuItem[]; label: string; disabled?: boolean; align?: 'start' | 'end'; buttonClass?: string }>(),
  { disabled: false, align: 'start', buttonClass: '' },
)
const emit = defineEmits<{ select: [id: string] }>()

const menuId = useId()
const open = ref(false)
const root = ref<HTMLElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
const itemRefs = ref<HTMLButtonElement[]>([])

const radio = computed(() => props.items.some((item) => item.checked !== undefined))

function enabledIndexes(): number[] {
  return props.items.flatMap((item, index) => (item.disabled ? [] : [index]))
}

async function show(focus: 'first' | 'last' | 'checked' = 'first'): Promise<void> {
  if (props.disabled) return
  open.value = true
  document.addEventListener('pointerdown', onOutside, true)
  await nextTick()
  const enabled = enabledIndexes()
  const checked = props.items.findIndex((item) => item.checked && !item.disabled)
  const index = focus === 'checked' && checked >= 0 ? checked : focus === 'last' ? enabled[enabled.length - 1] : enabled[0]
  if (index !== undefined) itemRefs.value[index]?.focus()
}

function hide(returnFocus: boolean): void {
  if (!open.value) return
  open.value = false
  document.removeEventListener('pointerdown', onOutside, true)
  if (returnFocus) trigger.value?.focus()
}

function onOutside(event: PointerEvent): void {
  if (root.value && !root.value.contains(event.target as Node)) hide(false)
}

onBeforeUnmount(() => document.removeEventListener('pointerdown', onOutside, true))

function onTriggerClick(): void {
  if (open.value) hide(true)
  else void show(radio.value ? 'checked' : 'first')
}

function onTriggerKeydown(event: KeyboardEvent): void {
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    void show(event.key === 'ArrowUp' ? 'last' : radio.value ? 'checked' : 'first')
  }
}

function move(from: number, step: number): void {
  const enabled = enabledIndexes()
  if (!enabled.length) return
  const at = enabled.indexOf(from)
  const next = enabled[(at + step + enabled.length) % enabled.length]
  itemRefs.value[next]?.focus()
}

function onMenuKeydown(event: KeyboardEvent, index: number): void {
  const enabled = enabledIndexes()
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      move(index, 1)
      break
    case 'ArrowUp':
      event.preventDefault()
      move(index, -1)
      break
    case 'Home':
      event.preventDefault()
      itemRefs.value[enabled[0]]?.focus()
      break
    case 'End':
      event.preventDefault()
      itemRefs.value[enabled[enabled.length - 1]]?.focus()
      break
    case 'Escape':
      event.preventDefault()
      event.stopPropagation()
      hide(true)
      break
    case 'Tab':
      hide(false)
      break
  }
}

function pick(item: MenuItem): void {
  if (item.disabled) return
  hide(true)
  emit('select', item.id)
}

defineExpose({ show })
</script>

<template>
  <div ref="root" class="menu-root">
    <button
      ref="trigger"
      type="button"
      class="menu-trigger"
      :class="buttonClass"
      aria-haspopup="menu"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-controls="open ? menuId : undefined"
      :aria-label="label"
      :disabled="disabled"
      @click="onTriggerClick"
      @keydown="onTriggerKeydown"
    >
      <slot />
    </button>
    <div v-if="open" :id="menuId" class="menu" :class="`menu--${align}`" role="menu" :aria-label="label">
      <button
        v-for="(item, index) in items"
        :key="item.id"
        ref="itemRefs"
        type="button"
        class="menu__item"
        :role="item.checked === undefined ? 'menuitem' : 'menuitemradio'"
        :aria-checked="item.checked === undefined ? undefined : item.checked ? 'true' : 'false'"
        :aria-disabled="item.disabled ? 'true' : undefined"
        tabindex="-1"
        :data-item="item.id"
        @click="pick(item)"
        @keydown="onMenuKeydown($event, index)"
      >
        <span v-if="radio" class="menu__check" aria-hidden="true">
          <svg v-if="item.checked" viewBox="0 0 16 16" width="12" height="12">
            <path d="M3 8.5l3 3 7-7" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        {{ item.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.menu-root {
  position: relative;
  display: inline-flex;
}

.menu-trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 32px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  color: var(--text-primary);
  font: inherit;
  font-size: var(--text-sm);
  cursor: pointer;
}

.menu-trigger:hover:not(:disabled) {
  border-color: var(--border-strong);
}

.menu-trigger:disabled {
  cursor: not-allowed;
  background: var(--surface-sunken);
  border-color: var(--border-subtle);
  color: var(--text-muted);
}

.menu {
  position: absolute;
  top: calc(100% + var(--space-1));
  z-index: 60;
  display: grid;
  min-width: 200px;
  padding: var(--space-1);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.menu--start {
  left: 0;
}

.menu--end {
  right: 0;
}

.menu__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-primary);
  font: inherit;
  font-size: var(--text-sm);
  text-align: left;
  white-space: nowrap;
  cursor: pointer;
}

.menu__item:hover,
.menu__item:focus-visible {
  background: var(--surface-sunken);
}

.menu__item[aria-disabled='true'] {
  color: var(--text-muted);
  cursor: not-allowed;
}

.menu__check {
  display: inline-grid;
  place-items: center;
  width: 12px;
  color: var(--accent);
}
</style>
