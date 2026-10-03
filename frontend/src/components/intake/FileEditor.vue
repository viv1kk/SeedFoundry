<script setup lang="ts">
// The editor (ui-spec.md section 2, FR-IN-4 to FR-IN-6): name field and category picker,
// then the toolbar (Edit / Preview, mic, overflow menu), then the text. The name is saved on
// Enter or when the field loses focus; Escape puts it back. The category picker is a menu,
// not a select, so arrowing through it changes nothing until a choice is made (D-42).
// Edit is a plain textarea in the mono face (NFR-3, D-41).
import { computed, nextTick, ref, watch } from 'vue'
import { ApiError, messageOf } from '../../api'
import { useIntakeStore } from '../../stores/intake'
import { useLabStore } from '../../stores/lab'
import BaseConfirm from '../base/BaseConfirm.vue'
import BaseMenu, { type MenuItem } from '../base/BaseMenu.vue'
import BaseTooltip from '../base/BaseTooltip.vue'
import MarkdownPreview from './MarkdownPreview.vue'

const props = defineProps<{ fileId: string; readOnly: boolean }>()

const lab = useLabStore()
const intake = useIntakeStore()

const file = computed(() => lab.file(props.fileId))
const mode = ref<'edit' | 'preview'>('edit')
const textarea = ref<HTMLTextAreaElement | null>(null)
const nameInput = ref<HTMLInputElement | null>(null)
const categoryMenu = ref<InstanceType<typeof BaseMenu> | null>(null)

// Name field
const name = ref('')
const nameError = ref<string | null>(null)
const actionError = ref<string | null>(null)
let editingName = false

watch(
  () => [props.fileId, file.value?.name] as const,
  ([id], previous) => {
    if (previous && id !== previous[0]) {
      editingName = false
      nameError.value = null
      actionError.value = null
      if (textarea.value) textarea.value.scrollTop = 0
    }
    if (!editingName) name.value = file.value?.name ?? ''
  },
  { immediate: true },
)

function onNameInput(event: Event): void {
  editingName = true
  name.value = (event.target as HTMLInputElement).value
}

async function commitName(): Promise<void> {
  const current = file.value
  if (!current || !editingName) return
  if (name.value === current.name) {
    editingName = false
    nameError.value = null
    return
  }
  try {
    const saved = await intake.rename(current.id, name.value)
    editingName = false
    nameError.value = null
    name.value = saved.name
  } catch (error) {
    nameError.value = messageOf(error)
  }
}

function revertName(): void {
  editingName = false
  nameError.value = null
  name.value = file.value?.name ?? ''
}

function onNameKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter') {
    event.preventDefault()
    void commitName()
  } else if (event.key === 'Escape' && editingName) {
    event.preventDefault()
    revertName()
  }
}

// Category
const categoryItems = computed<MenuItem[]>(() =>
  intake.categories.map((c) => ({ id: c.id, label: c.label, checked: c.id === file.value?.category })),
)
const categoryLabel = computed(() => intake.labelOf(file.value?.category ?? ''))

const replacing = ref<{ category: string; holder: string; message: string } | null>(null)
const replaceBusy = ref(false)

function replaceQuestion(categoryId: string, holder: string): string {
  return `${intake.labelOf(categoryId)} already has ${holder}. Replace it with ${file.value?.name ?? ''}?`
}

async function chooseCategory(categoryId: string, replace = false): Promise<void> {
  const current = file.value
  if (!current || categoryId === current.category) return
  actionError.value = null
  const holder = intake.slotHolder(categoryId, current.id)
  if (holder && !replace) {
    replacing.value = { category: categoryId, holder: holder.name, message: replaceQuestion(categoryId, holder.name) }
    return
  }
  try {
    await intake.recategorise(current.id, categoryId, replace)
    replacing.value = null
  } catch (error) {
    // The server is the backstop for FR-IN-3 (D-35): ask with its own words.
    if (error instanceof ApiError && error.code === 'core_slot_taken') {
      const existing = (error.detail.existing as { name?: string } | undefined)?.name ?? ''
      replacing.value = { category: categoryId, holder: existing, message: error.message }
    } else {
      replacing.value = null
      actionError.value = messageOf(error)
    }
  }
}

async function confirmReplace(): Promise<void> {
  if (!replacing.value) return
  replaceBusy.value = true
  try {
    await chooseCategory(replacing.value.category, true)
  } finally {
    replaceBusy.value = false
  }
}

// Overflow menu
const overflowItems = computed<MenuItem[]>(() => [
  { id: 'rename', label: 'Rename', disabled: props.readOnly },
  { id: 'category', label: 'Change category', disabled: props.readOnly },
  { id: 'delete', label: 'Delete', disabled: props.readOnly },
])

const deleting = ref(false)
const deleteBusy = ref(false)
const deleteError = ref<string | null>(null)

async function onOverflow(id: string): Promise<void> {
  if (id === 'rename') {
    await nextTick()
    nameInput.value?.focus()
    nameInput.value?.select()
  } else if (id === 'category') {
    await nextTick()
    void categoryMenu.value?.show('checked')
  } else if (id === 'delete') {
    deleteError.value = null
    deleting.value = true
  }
}

async function confirmDelete(): Promise<void> {
  const current = file.value
  if (!current) return
  deleteBusy.value = true
  try {
    await intake.remove(current.id)
    deleting.value = false
  } catch (error) {
    deleteError.value = messageOf(error)
  } finally {
    deleteBusy.value = false
  }
}

// Text
const text = computed(() => intake.text(props.fileId))
const saveError = computed(() => intake.saveError(props.fileId))

function onInput(event: Event): void {
  intake.edit(props.fileId, (event.target as HTMLTextAreaElement).value)
}
</script>

<template>
  <section v-if="file" class="editor" aria-label="Editor" data-test="editor">
    <div class="editor__meta">
      <label class="field field--name">
        <span class="caps-label">Name</span>
        <input
          ref="nameInput"
          class="field__input"
          :value="name"
          maxlength="120"
          spellcheck="false"
          autocomplete="off"
          :readonly="readOnly"
          :aria-invalid="nameError ? 'true' : undefined"
          data-test="name"
          @input="onNameInput"
          @keydown="onNameKeydown"
          @blur="commitName"
        />
      </label>
      <div class="field">
        <span class="caps-label" aria-hidden="true">Category</span>
        <BaseMenu
          ref="categoryMenu"
          :items="categoryItems"
          :label="`Category: ${categoryLabel}`"
          :disabled="readOnly"
          button-class="category-trigger"
          data-test="category"
          @select="chooseCategory"
        >
          <span>{{ categoryLabel }}</span>
          <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
            <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </BaseMenu>
      </div>
    </div>
    <p v-if="nameError" class="editor__error" role="alert" data-test="name-error">{{ nameError }}</p>
    <p v-if="actionError" class="editor__error" role="alert" data-test="action-error">{{ actionError }}</p>

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
      <p v-if="saveError" class="editor__error editor__error--inline" role="alert" data-test="save-error">{{ saveError }}</p>
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
        <BaseMenu
          :items="overflowItems"
          :label="`More actions for ${file.name}`"
          align="end"
          button-class="icon-button"
          data-test="overflow"
          @select="onOverflow"
        >
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
            <circle cx="3.5" cy="8" r="1.25" fill="currentColor" />
            <circle cx="8" cy="8" r="1.25" fill="currentColor" />
            <circle cx="12.5" cy="8" r="1.25" fill="currentColor" />
          </svg>
        </BaseMenu>
      </div>
    </div>

    <div class="editor__body">
      <textarea
        v-if="mode === 'edit'"
        ref="textarea"
        class="editor__text"
        :value="text"
        :readonly="readOnly"
        :aria-label="`Content of ${file.name}`"
        spellcheck="false"
        autocapitalize="off"
        autocomplete="off"
        wrap="soft"
        data-test="text"
        @input="onInput"
      />
      <MarkdownPreview v-else :text="text" :label="`Preview of ${file.name}`" />
    </div>

    <BaseConfirm
      :open="replacing !== null"
      title="Replace it?"
      :confirm-label="replacing ? `Replace ${replacing.holder}` : 'Replace'"
      :busy="replaceBusy"
      @confirm="confirmReplace"
      @cancel="replacing = null"
    >
      <p>{{ replacing?.message }}</p>
      <p>{{ replacing?.holder }} will be deleted.</p>
    </BaseConfirm>

    <BaseConfirm
      :open="deleting"
      :title="`Delete ${file.name}?`"
      confirm-label="Delete"
      :busy="deleteBusy"
      :error="deleteError"
      @confirm="confirmDelete"
      @cancel="deleting = false"
    >
      <p>This removes {{ file.name }} from Knowledge. It cannot be undone.</p>
    </BaseConfirm>
  </section>
</template>

<style scoped>
.editor {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
}

.editor__meta {
  display: flex;
  align-items: flex-end;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6) var(--space-2);
}

.field {
  display: grid;
  gap: var(--space-1);
}

.field--name {
  flex: 1;
  max-width: 480px;
}

.field__input {
  min-height: 32px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.field__input:hover:not([readonly]) {
  border-color: var(--border-strong);
}

.field__input[readonly] {
  background: var(--surface-sunken);
  color: var(--text-secondary);
}

.field__input[aria-invalid='true'] {
  border-color: var(--status-negative);
}

.field :deep(.category-trigger) {
  min-width: 200px;
  justify-content: space-between;
}

.editor__error {
  padding: 0 var(--space-6);
  color: var(--status-negative);
  font-size: var(--text-sm);
}

.editor__error--inline {
  flex: 1;
  padding: 0;
  text-align: right;
}

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

.editor__text:focus-visible {
  outline-offset: -2px;
}

.editor__text[readonly] {
  background: var(--surface-base);
  color: var(--text-secondary);
}
</style>
