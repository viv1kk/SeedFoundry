<script setup lang="ts">
// The markdown editor itself (FR-IN-4, FR-IN-5, FR-RB-1): the Edit / Preview toggle, the mic icon,
// then the text, as a plain textarea in the mono face (NFR-3, D-41) or the sanitised Preview (D-40).
// The Knowledge editor (FileEditor) and the rebuild modal (D-19) both use it; each puts its own
// controls in the `status` and `tools` slots.
import { ref } from 'vue'
import BaseTooltip from '../base/BaseTooltip.vue'
import MarkdownPreview from './MarkdownPreview.vue'

withDefaults(defineProps<{ text: string; label: string; readOnly?: boolean; placeholder?: string }>(), {
  readOnly: false,
  placeholder: undefined,
})
const emit = defineEmits<{ input: [value: string] }>()

const mode = ref<'edit' | 'preview'>('edit')
const textarea = ref<HTMLTextAreaElement | null>(null)

defineExpose({
  scrollToTop(): void {
    if (textarea.value) textarea.value.scrollTop = 0
  },
})
</script>

<template>
  <!-- Two root nodes, no wrapper: the toolbar and the body sit directly in the host's flex column. -->
  <div class="editor__toolbar">
    <div class="segmented" role="group" aria-label="View">
      <button
        type="button"
        class="segmented__option"
        :aria-pressed="mode === 'edit' ? 'true' : 'false'"
        data-test="mode-edit"
        @click="mode = 'edit'"
      >
        Edit
      </button>
      <button
        type="button"
        class="segmented__option"
        :aria-pressed="mode === 'preview' ? 'true' : 'false'"
        data-test="mode-preview"
        @click="mode = 'preview'"
      >
        Preview
      </button>
    </div>
    <slot name="status" />
    <div class="editor__tools">
      <!-- Voice input is a visual mic icon only (D-8a): the button does nothing. -->
      <BaseTooltip text="Voice input">
        <button type="button" class="icon-button" aria-label="Voice input" data-test="mic">
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
            <rect x="5.5" y="1.5" width="5" height="8" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.5" />
            <path d="M3 7.5a5 5 0 0 0 10 0M8 12.5v2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </button>
      </BaseTooltip>
      <slot name="tools" />
    </div>
  </div>

  <div class="editor__body">
    <textarea
      v-if="mode === 'edit'"
      ref="textarea"
      class="editor__text"
      :value="text"
      :readonly="readOnly"
      :placeholder="placeholder"
      :aria-label="label"
      spellcheck="false"
      autocapitalize="off"
      autocomplete="off"
      wrap="soft"
      data-test="text"
      @input="emit('input', ($event.target as HTMLTextAreaElement).value)"
    />
    <MarkdownPreview v-else :text="text" :label="label.replace(/^Content of/, 'Preview of')" />
  </div>
</template>

<style scoped>
.editor__toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-6);
  border-bottom: 1px solid var(--border-subtle);
}

.editor__tools {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-left: auto;
}

.segmented {
  display: inline-flex;
  padding: 2px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-sunken);
}

.segmented__option {
  min-height: 26px;
  padding: 0 var(--space-3);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
}

.segmented__option[aria-pressed='true'] {
  background: var(--surface-raised);
  border-color: var(--border-default);
  color: var(--text-primary);
  font-weight: 600;
}

.icon-button,
.editor__tools :deep(.icon-button) {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  min-height: 32px;
  padding: 0;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  color: var(--text-secondary);
  cursor: pointer;
}

.icon-button:hover,
.editor__tools :deep(.icon-button:hover) {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.editor__body {
  flex: 1;
  min-height: 0;
}

.editor__text {
  display: block;
  width: 100%;
  height: 100%;
  padding: var(--space-6) var(--space-8);
  border: 0;
  resize: none;
  background: var(--surface-raised);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.6;
  tab-size: 2;
}

.editor__text::placeholder {
  color: var(--text-muted);
}

.editor__text:focus-visible {
  outline-offset: -2px;
}

.editor__text[readonly] {
  background: var(--surface-base);
  color: var(--text-secondary);
}
</style>
