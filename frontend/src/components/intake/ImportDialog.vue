<script setup lang="ts">
// Import (FR-IN-7, FR-IN-11, ui-spec.md section 2): one row per chosen file with its
// category pre-selected from the server's filename hints (else the first open initiation file,
// D-84), the name it will take (D-85), and "Replaces existing Identity.md" when the file would
// take a core slot that has one. Two rows set to the same core category
// block Import until one changes (D-42). Import sends one request per file, its raw bytes as
// the body (D-34), in row order; the server's refusals (413 file_too_large, 415 not_utf8_text,
// 415 not_markdown) show on their row as written.
import { computed, ref, watch } from 'vue'
import { messageOf } from '../../api'
import { useIntakeStore } from '../../stores/intake'
import BaseButton from '../base/BaseButton.vue'
import BaseChip from '../base/BaseChip.vue'
import BaseModal from '../base/BaseModal.vue'

const props = defineProps<{ open: boolean; files: File[] }>()
const emit = defineEmits<{ close: []; imported: [id: string] }>()

const intake = useIntakeStore()

interface Row {
  key: number
  file: File
  category: string
  status: 'pending' | 'done' | 'error'
  error: string | null
}

const rows = ref<Row[]>([])
const busy = ref(false)

watch(
  () => [props.open, props.files] as const,
  ([open, files]) => {
    if (!open) return
    // A file with no hint takes the next initiation file that is neither added nor hinted by another
    // row, so it does not clash with them.
    const taken = files.filter((file) => intake.hasHint(file.name)).map((file) => intake.hintFor(file.name))
    rows.value = files.map((file, key) => {
      const category = intake.hintFor(file.name, taken)
      if (!intake.hasHint(file.name)) taken.push(category)
      return { key, file, category, status: 'pending' as const, error: null }
    })
  },
  { immediate: true },
)

/** Another pending row set to the same core category, if any. */
function clash(row: Row): Row | undefined {
  if (row.status === 'done' || !intake.isCore(row.category)) return undefined
  return rows.value.find((other) => other !== row && other.status !== 'done' && other.category === row.category)
}

function replaces(row: Row): string | null {
  if (row.status === 'done') return null
  return intake.slotHolder(row.category)?.name ?? null
}

function setCategory(row: Row, value: string): void {
  row.category = value
  if (row.status === 'error') {
    row.status = 'pending'
    row.error = null
  }
}

const pending = computed(() => rows.value.filter((row) => row.status === 'pending'))
const blocked = computed(() => rows.value.some((row) => clash(row)))
const anyDone = computed(() => rows.value.some((row) => row.status === 'done'))
const canImport = computed(() => pending.value.length > 0 && !blocked.value && !busy.value)

async function runImport(): Promise<void> {
  if (!canImport.value) return
  busy.value = true
  let first: string | null = null
  for (const row of pending.value) {
    const holder = replaces(row)
    try {
      const file = await intake.importFile(row.file, row.file.name, row.category, holder !== null)
      row.status = 'done'
      first ??= file.id
    } catch (error) {
      row.status = 'error'
      row.error = messageOf(error)
    }
  }
  busy.value = false
  if (first) emit('imported', first)
  if (rows.value.every((row) => row.status === 'done')) emit('close')
}
</script>

<template>
  <BaseModal :open="open" title="Import files" size="md" @close="emit('close')">
    <p class="intro">Choose an initiation file for each file. Each holds one file, and takes its name.</p>
    <ul class="rows" data-test="import-rows">
      <li v-for="row in rows" :key="row.key" class="row" :data-row="row.file.name">
        <div class="row__main">
          <span class="row__name">{{ row.file.name }}</span>
          <BaseChip v-if="row.status === 'done'" tone="positive" data-test="row-done">Imported</BaseChip>
          <select
            v-else
            class="row__select"
            :value="row.category"
            :aria-label="`Category for ${row.file.name}`"
            :disabled="busy"
            data-test="row-category"
            @change="setCategory(row, ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="c in intake.categories" :key="c.id" :value="c.id">{{ c.label }}</option>
          </select>
        </div>
        <p v-if="row.status !== 'done'" class="row__note" data-test="row-takes">Becomes {{ intake.suggestedName(row.category) }}</p>
        <p v-if="clash(row)" class="row__note row__note--warning" data-test="row-clash">
          Only one {{ intake.labelOf(row.category) }} file: {{ clash(row)?.file.name }} is also set to it.
        </p>
        <p v-else-if="replaces(row)" class="row__note row__note--warning" data-test="row-replace">
          Replaces existing {{ replaces(row) }}
        </p>
        <p v-if="row.error" class="row__note row__note--error" role="alert" data-test="row-error">{{ row.error }}</p>
      </li>
    </ul>
    <template #footer>
      <BaseButton data-test="import-cancel" @click="emit('close')">{{ anyDone ? 'Close' : 'Cancel' }}</BaseButton>
      <BaseButton variant="primary" :disabled="!canImport" data-test="import-confirm" @click="runImport">Import</BaseButton>
    </template>
  </BaseModal>
</template>

<style scoped>
.intro {
  margin-bottom: var(--space-3);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.rows {
  display: grid;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.row {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
}

.row__main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.row__name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.row__select {
  min-height: 30px;
  min-width: 190px;
  padding: 0 var(--space-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  color: var(--text-primary);
  font: inherit;
  font-size: var(--text-sm);
}

.row__note {
  font-size: var(--text-sm);
}

.row__note--warning {
  color: var(--status-warning);
  font-weight: 600;
}

.row__note--error {
  color: var(--status-negative);
}
</style>
