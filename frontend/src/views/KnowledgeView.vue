<script setup lang="ts">
// Knowledge (code: intake), ui-spec.md section 2: the editor left, the file panel right
// (FR-IN-1). The selected file is in the URL (?file=f-3), so a refresh keeps it; switching
// files replaces the URL rather than adding history (D-42). While a build runs the page is
// read-only with a banner (FR-B-8).
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import EmptyState from '../components/intake/EmptyState.vue'
import FileEditor from '../components/intake/FileEditor.vue'
import FilePanel from '../components/intake/FilePanel.vue'
import ImportDialog from '../components/intake/ImportDialog.vue'
import NewFileDialog from '../components/intake/NewFileDialog.vue'
import { useIntakeStore } from '../stores/intake'
import { useLabStore } from '../stores/lab'

const lab = useLabStore()
const intake = useIntakeStore()
const route = useRoute()
const router = useRouter()

const readOnly = computed(() => lab.runningBuild !== null)
const loaded = computed(() => lab.snapshot !== null)

// Selection
const queryFile = computed(() => (typeof route.query.file === 'string' ? route.query.file : null))
const selectedId = computed(() => (lab.file(queryFile.value) ? queryFile.value : null))

function select(id: string | null): void {
  if (id === queryFile.value) return
  const query = { ...route.query }
  if (id) query.file = id
  else delete query.file
  void router.replace({ query })
}

// No selection, or a file that is gone: select the first file in Ensemble order.
watch(
  [loaded, queryFile, () => intake.orderedFiles.map((f) => f.id).join(',')],
  () => {
    if (!loaded.value || selectedId.value) return
    select(intake.orderedFiles[0]?.id ?? null)
  },
  { immediate: true },
)

// Autosave on file switch (FR-IN-6), however the switch happens.
watch(selectedId, (_, previous) => {
  void intake.flush(previous)
})

onBeforeRouteLeave(() => {
  void intake.flushAll()
})

function onBeforeUnload(event: BeforeUnloadEvent): void {
  if (intake.flushOnUnload()) {
    event.preventDefault()
    event.returnValue = ''
  }
}

onMounted(() => {
  void intake.loadCategories()
  window.addEventListener('beforeunload', onBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
})

// New file
const newOpen = ref(false)
const newCategory = ref<string | null>(null)

function openNew(category?: string): void {
  newCategory.value = category ?? null
  newOpen.value = true
}

// Import
const picker = ref<HTMLInputElement | null>(null)
const importFiles = ref<File[]>([])
const importOpen = ref(false)

function openImport(): void {
  picker.value?.click()
}

function onPicked(event: Event): void {
  const input = event.target as HTMLInputElement
  const chosen = Array.from(input.files ?? [])
  input.value = ''
  if (!chosen.length) return
  importFiles.value = chosen
  importOpen.value = true
}

const runningIteration = computed(() => lab.runningBuild?.iteration ?? 1)
</script>

<template>
  <div class="knowledge" :class="{ 'knowledge--locked': readOnly }" data-test="knowledge">
    <div v-if="readOnly" class="banner" role="status" data-test="read-only-banner">
      <span>A build is running. Knowledge files are read-only until it finishes.</span>
      <RouterLink :to="`/build/${runningIteration}`" class="banner__link">Go to the build</RouterLink>
    </div>
    <div class="knowledge__layout">
      <div class="knowledge__editor">
        <FileEditor v-if="selectedId" :file-id="selectedId" :read-only="readOnly" />
        <EmptyState v-else-if="loaded && !lab.files.length" :read-only="readOnly" @new="openNew()" @import="openImport" />
        <p v-else-if="!loaded" class="knowledge__loading">Loading knowledge files</p>
      </div>
      <FilePanel
        :selected-id="selectedId"
        :read-only="readOnly"
        :build-note="intake.buildNote"
        @select="select"
        @new="openNew"
        @import="openImport"
        @start-build="intake.startBuild"
      />
    </div>

    <input
      ref="picker"
      type="file"
      accept=".md,text/markdown"
      multiple
      class="visually-hidden"
      tabindex="-1"
      aria-hidden="true"
      data-test="import-input"
      @change="onPicked"
    />
    <NewFileDialog :open="newOpen" :initial-category="newCategory" @close="newOpen = false" @created="select" />
    <ImportDialog :open="importOpen" :files="importFiles" @close="importOpen = false" @imported="select" />
  </div>
</template>

<style scoped>
.knowledge {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--top-bar-height));
}

.knowledge__layout {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(300px, 3fr);
  flex: 1;
  min-height: 0;
}

.knowledge__editor {
  min-width: 0;
  min-height: 0;
  overflow: auto;
}

.knowledge__loading {
  padding: var(--space-12) var(--space-8);
  color: var(--text-secondary);
}

.banner {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-6);
  background: var(--accent-subtle);
  border-bottom: 1px solid var(--accent);
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.banner__link {
  font-weight: 600;
}
</style>
