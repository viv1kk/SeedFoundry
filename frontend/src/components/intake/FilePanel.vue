<script setup lang="ts">
// The file panel (ui-spec.md section 2): the core checklist and Start Build (FR-IN-8,
// FR-IN-9), then the files grouped by category in Ensemble order, with the unsaved dot
// (FR-IN-6) and a muted "Add file" link in each empty category.
import { computed } from 'vue'
import { useIntakeStore } from '../../stores/intake'
import { useLabStore } from '../../stores/lab'
import BaseButton from '../base/BaseButton.vue'
import BaseTooltip from '../base/BaseTooltip.vue'

defineProps<{ selectedId: string | null; readOnly: boolean; buildNote: string | null }>()
const emit = defineEmits<{ select: [id: string]; new: [category?: string]; import: []; startBuild: [] }>()

const lab = useLabStore()
const intake = useIntakeStore()

const missingText = computed(() => `Missing: ${intake.missing.join(', ')}`)

const groups = computed(() =>
  intake.categories.map((category) => ({
    category,
    files: intake.orderedFiles.filter((file) => file.category === category.id),
  })),
)
</script>

<template>
  <aside class="panel" aria-label="Knowledge files" data-test="file-panel">
    <section class="panel__section" aria-labelledby="core-heading">
      <h2 id="core-heading" class="caps-label">Core files</h2>
      <ul class="checklist" data-test="checklist">
        <li
          v-for="slot in intake.coreSlots"
          :key="slot.category.id"
          class="checklist__item"
          :class="{ 'checklist__item--complete': slot.complete }"
          :data-slot="slot.category.id"
          :data-complete="slot.complete ? 'true' : 'false'"
        >
          <span class="checklist__box" aria-hidden="true">
            <svg v-if="slot.complete" viewBox="0 0 16 16" width="12" height="12">
              <path d="M3 8.5l3 3 7-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <span>{{ slot.category.label }}</span>
          <span class="visually-hidden">{{ slot.complete ? ', complete' : ', missing' }}</span>
        </li>
      </ul>
      <BaseTooltip v-if="!intake.ready" :text="missingText" class="start-build">
        <BaseButton variant="primary" disabled explain-disabled class="start-build__button" data-test="start-build">
          Start Build
        </BaseButton>
      </BaseTooltip>
      <BaseButton
        v-else
        variant="primary"
        :disabled="readOnly"
        class="start-build start-build__button"
        data-test="start-build"
        @click="emit('startBuild')"
      >
        Start Build
      </BaseButton>
      <p class="panel__note" role="status" data-test="build-note">{{ buildNote ?? '' }}</p>
    </section>

    <section class="panel__section panel__section--files" aria-labelledby="files-heading">
      <div class="files__header">
        <h2 id="files-heading" class="caps-label">Files</h2>
        <div class="files__actions">
          <BaseButton :disabled="readOnly" data-test="new-file" @click="emit('new')">
            <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
              <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" />
            </svg>
            New
          </BaseButton>
          <BaseButton :disabled="readOnly" data-test="import" @click="emit('import')">Import</BaseButton>
        </div>
      </div>

      <div v-for="group in groups" :key="group.category.id" class="group" :data-category="group.category.id">
        <h3 class="group__title">{{ group.category.label }}</h3>
        <ul v-if="group.files.length" class="group__files">
          <li v-for="file in group.files" :key="file.id">
            <button
              type="button"
              class="file"
              :class="{ 'file--selected': file.id === selectedId }"
              :aria-current="file.id === selectedId ? 'true' : undefined"
              :data-file="file.id"
              @click="emit('select', file.id)"
            >
              <span class="file__name">{{ file.name }}</span>
              <span v-if="intake.isDirty(file.id)" class="file__dot" data-test="unsaved-dot">
                <span class="visually-hidden">Unsaved changes</span>
              </span>
            </button>
          </li>
        </ul>
        <button
          v-else-if="!readOnly"
          type="button"
          class="group__add"
          :data-add="group.category.id"
          @click="emit('new', group.category.id)"
        >
          Add file<span class="visually-hidden"> to {{ group.category.label }}</span>
        </button>
        <p v-else class="group__empty">No file</p>
      </div>
      <p v-if="intake.categoriesError" class="panel__error" role="alert">{{ intake.categoriesError }}</p>
      <p v-else-if="!lab.snapshot" class="panel__note">Loading files</p>
    </section>
  </aside>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: auto;
  background: var(--surface-raised);
  border-left: 1px solid var(--border-default);
}

.panel__section {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
}

.panel__section + .panel__section {
  border-top: 1px solid var(--border-subtle);
}

.panel__section--files {
  align-content: start;
}

.checklist {
  display: grid;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.checklist__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.checklist__item--complete {
  color: var(--text-primary);
  font-weight: 600;
}

.checklist__box {
  display: inline-grid;
  place-items: center;
  width: 16px;
  height: 16px;
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-sm);
  color: var(--text-inverse);
}

.checklist__item--complete .checklist__box {
  border-color: var(--status-positive);
  background: var(--status-positive);
}

.start-build,
.start-build :deep(.start-build__button),
.start-build__button {
  width: 100%;
}

.panel__note {
  min-height: 1.5em;
  color: var(--text-secondary);
  font-size: var(--text-xs);
}

.panel__error {
  color: var(--status-negative);
  font-size: var(--text-sm);
}

.files__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.files__actions {
  display: flex;
  gap: var(--space-2);
}

.group {
  display: grid;
  gap: var(--space-1);
}

.group__title {
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
}

.group__files {
  display: grid;
  gap: 2px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.file {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-1) var(--space-2);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  text-align: left;
  cursor: pointer;
}

.file:hover {
  background: var(--surface-sunken);
}

.file--selected {
  background: var(--accent-subtle);
  border-color: var(--accent);
  font-weight: 600;
}

.file--selected:hover {
  background: var(--accent-subtle);
}

.file__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Unsaved changes (FR-IN-6): work in progress, so the accent */
.file__dot {
  flex: none;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
}

.group__add {
  justify-self: start;
  padding: var(--space-1) var(--space-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-size: var(--text-sm);
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.group__add:hover {
  color: var(--text-primary);
}

.group__empty {
  padding: var(--space-1) var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-sm);
}
</style>
