<script setup lang="ts">
// Preview (FR-IN-4): sanitised HTML from src/markdown.ts, which never emits a src or href
// (R-7, NFR-2, D-40). Body type; tables, code and the image and link stand-ins styled here.
import { computed } from 'vue'
import { renderMarkdown } from '../../markdown'

// `compact` fits the text to its content, for a quote inside a page (the report's observer feedback).
const props = defineProps<{ text: string; label: string; compact?: boolean }>()

// The only v-html in the app, and it only ever holds renderMarkdown's output.
const html = computed(() => renderMarkdown(props.text))
</script>

<template>
  <div class="markdown" :class="{ 'markdown--compact': compact }" tabindex="0" role="document" :aria-label="label" data-test="preview" v-html="html" />
</template>

<style scoped>
.markdown {
  height: 100%;
  overflow: auto;
  padding: var(--space-6) var(--space-8);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: var(--text-md);
  line-height: var(--line-height-body);
  overflow-wrap: anywhere;
}

.markdown--compact {
  height: auto;
  overflow: visible;
  padding: 0;
  font-size: var(--text-sm);
}

.markdown :deep(> :first-child) {
  margin-top: 0;
}

.markdown :deep(h1),
.markdown :deep(h2),
.markdown :deep(h3),
.markdown :deep(h4),
.markdown :deep(h5),
.markdown :deep(h6) {
  margin: var(--space-6) 0 var(--space-2);
  font-weight: 600;
  line-height: 1.25;
}

.markdown :deep(h1) {
  font-size: var(--text-xl);
}

.markdown :deep(h2) {
  font-size: var(--text-lg);
  padding-bottom: var(--space-1);
  border-bottom: 1px solid var(--border-subtle);
}

.markdown :deep(h3) {
  font-size: var(--text-md);
}

.markdown :deep(h4),
.markdown :deep(h5),
.markdown :deep(h6) {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.markdown :deep(p),
.markdown :deep(ul),
.markdown :deep(ol),
.markdown :deep(blockquote),
.markdown :deep(pre),
.markdown :deep(table) {
  margin: 0 0 var(--space-3);
}

.markdown :deep(ul),
.markdown :deep(ol) {
  padding-left: var(--space-6);
}

.markdown :deep(li + li) {
  margin-top: var(--space-1);
}

.markdown :deep(blockquote) {
  padding: var(--space-1) var(--space-4);
  border-left: 3px solid var(--border-default);
  color: var(--text-secondary);
}

.markdown :deep(hr) {
  margin: var(--space-6) 0;
  border: 0;
  border-top: 1px solid var(--border-default);
}

.markdown :deep(code) {
  padding: 1px var(--space-1);
  border-radius: var(--radius-sm);
  background: var(--surface-sunken);
  font-size: 0.9em;
}

.markdown :deep(pre) {
  overflow-x: auto;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-sunken);
  font-size: var(--text-sm);
  line-height: 1.5;
}

.markdown :deep(pre code) {
  padding: 0;
  background: transparent;
  font-size: inherit;
}

.markdown :deep(table) {
  display: block;
  max-width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.markdown :deep(th),
.markdown :deep(td) {
  padding: var(--space-1) var(--space-3);
  border: 1px solid var(--border-default);
  text-align: left;
}

.markdown :deep(th) {
  background: var(--surface-sunken);
  font-weight: 600;
}

.markdown :deep(.md-align-center) {
  text-align: center;
}

.markdown :deep(.md-align-right) {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Links are not followed in Preview (D-40): link style, then the address as text. */
.markdown :deep(.md-link) {
  color: var(--link);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown :deep(.md-address) {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.85em;
}

/* Images are not loaded (D-40): a labelled stand-in with the alt text and the address. */
.markdown :deep(.md-image) {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-1) var(--space-2);
  padding: var(--space-1) var(--space-2);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.markdown :deep(.md-image-label) {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
  color: var(--text-muted);
}
</style>
