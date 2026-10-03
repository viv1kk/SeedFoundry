<script setup lang="ts">
// Primary: the one main action in view (accent fill). Secondary: everything else.
// `explainDisabled` keeps a disabled button focusable (aria-disabled instead of disabled), so
// a tooltip that says why it is disabled can be reached from the keyboard (NFR-6).
const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary'
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
    explainDisabled?: boolean
  }>(),
  {
    variant: 'secondary',
    type: 'button',
    disabled: false,
    explainDisabled: false,
  },
)

const emit = defineEmits<{ click: [event: MouseEvent] }>()

function onClick(event: MouseEvent): void {
  if (props.disabled) {
    event.preventDefault()
    return
  }
  emit('click', event)
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled && !explainDisabled"
    :aria-disabled="disabled && explainDisabled ? 'true' : undefined"
    class="button"
    :class="`button--${variant}`"
    @click="onClick"
  >
    <slot />
  </button>
</template>

<style scoped>
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: 32px;
  padding: 0 var(--space-4);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
}

.button--primary {
  background: var(--accent);
  color: var(--text-inverse);
}

.button--primary:hover:not(:disabled, [aria-disabled='true']) {
  /* No colour shift: a lighter or darker accent would change the label's tested contrast. */
  box-shadow: var(--shadow-md);
}

.button--secondary {
  background: var(--surface-raised);
  border-color: var(--border-default);
  color: var(--text-primary);
}

.button--secondary:hover:not(:disabled, [aria-disabled='true']) {
  border-color: var(--border-strong);
  background: var(--surface-sunken);
}

.button:disabled,
.button[aria-disabled='true'] {
  cursor: not-allowed;
  background: var(--surface-sunken);
  border-color: var(--border-subtle);
  color: var(--text-muted);
}
</style>
