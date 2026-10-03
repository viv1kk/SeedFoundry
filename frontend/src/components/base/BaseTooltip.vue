<script setup lang="ts">
// A short text tip for the control in the default slot. It shows on hover and on keyboard
// focus, hides on leave, blur or Escape, and is linked to the control by aria-describedby.
import { onMounted, ref, useId } from 'vue'

// align 'end' keeps a tip on a control at the right edge of the window inside the window.
withDefaults(defineProps<{ text: string; placement?: 'top' | 'bottom'; align?: 'center' | 'end' }>(), {
  placement: 'bottom',
  align: 'center',
})

const id = useId()
const anchor = ref<HTMLElement | null>(null)
const visible = ref(false)

onMounted(() => {
  const control = anchor.value?.querySelector<HTMLElement>('a, button, input, select, textarea, [tabindex]')
  control?.setAttribute('aria-describedby', id)
})

function show(): void {
  visible.value = true
}

function hide(): void {
  visible.value = false
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && visible.value) hide()
}
</script>

<template>
  <span
    ref="anchor"
    class="tooltip-anchor"
    @mouseenter="show"
    @mouseleave="hide"
    @focusin="show"
    @focusout="hide"
    @keydown="onKeydown"
  >
    <slot />
    <span :id="id" role="tooltip" class="tooltip" :class="[`tooltip--${placement}`, `tooltip--${align}`, { 'tooltip--visible': visible }]">
      {{ text }}
    </span>
  </span>
</template>

<style scoped>
.tooltip-anchor {
  position: relative;
  display: inline-flex;
}

.tooltip {
  position: absolute;
  z-index: 50;
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-overlay);
  box-shadow: var(--shadow-sm);
  color: var(--text-primary);
  font-size: var(--text-xs);
  line-height: 1.4;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition: opacity var(--duration-fast) var(--ease-out);
}

.tooltip--center {
  left: 50%;
  transform: translateX(-50%);
}

.tooltip--end {
  right: 0;
}

.tooltip--bottom {
  top: calc(100% + var(--space-2));
}

.tooltip--top {
  bottom: calc(100% + var(--space-2));
}

.tooltip--visible {
  opacity: 1;
  visibility: visible;
}
</style>
