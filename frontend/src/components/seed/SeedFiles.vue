<script setup lang="ts">
// The Seed's files (FR-F-3, AC-4, ui-spec.md section 7, D-74, D-75): a card each for core.md,
// adaptation.md and protection.md with what the layer holds (never which Knowledge file fed it, D-9),
// its size, Preview and Download, then Download all (.zip). Preview opens the file in a modal through
// the Knowledge Preview's sanitiser (D-40); downloads are links to the server's relative /api URLs,
// which send each file and the zip as attachments, so nothing is fetched from anywhere else (NFR-2).
import { computed, ref } from 'vue'
import { size, type SeedFile, type SeedPackage } from '../../seed'
import BaseButton from '../base/BaseButton.vue'
import BaseModal from '../base/BaseModal.vue'
import MarkdownPreview from '../intake/MarkdownPreview.vue'

const props = defineProps<{ seed: SeedPackage; headingLevel?: 2 | 3 }>()

const previewing = ref<string | null>(null)
const shown = computed<SeedFile | null>(() => props.seed.files.find((f) => f.name === previewing.value) ?? null)
</script>

<template>
  <div class="files" data-test="seed-files">
    <ul class="files__cards">
      <li v-for="file in seed.files" :key="file.name" class="files__card" :data-file="file.name" data-test="seed-file">
        <component :is="`h${(headingLevel ?? 2) + 1}`" class="files__name">{{ file.name }}</component>
        <p class="files__description" data-test="seed-file-description">{{ file.description }}</p>
        <p class="files__size" data-test="seed-file-size">{{ size(file.bytes) }}</p>
        <div class="files__actions">
          <BaseButton data-action="preview" :aria-label="`Preview ${file.name}`" @click="previewing = file.name">Preview</BaseButton>
          <a class="files__download" :href="file.url" :download="file.name" data-action="download" :aria-label="`Download ${file.name}`">Download</a>
        </div>
      </li>
    </ul>
    <p class="files__all">
      <a class="files__download files__download--primary" :href="seed.zip.url" :download="seed.zip.name" data-action="download-zip">Download all (.zip)</a>
      <span class="files__size">{{ seed.zip.name }}, {{ size(seed.zip.bytes) }}</span>
    </p>

    <BaseModal :open="shown !== null" :title="shown ? `Preview: ${shown.name}` : 'Preview'" size="lg" name="seed-preview" @close="previewing = null">
      <MarkdownPreview v-if="shown" :text="shown.content" :label="`${shown.name}, preview`" />
    </BaseModal>
  </div>
</template>

<style scoped>
.files {
  display: grid;
  gap: var(--space-4);
}

.files__cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin: 0;
  padding: 0;
  list-style: none;
}

.files__card {
  display: grid;
  grid-template-rows: auto 1fr auto auto;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}

.files__name {
  font-family: var(--font-mono);
  font-size: var(--text-md);
  font-weight: 600;
}

.files__description {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.files__size {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.files__actions,
.files__all {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-3);
}

/* Links that save a file, drawn as BaseButton draws its two variants. */
.files__download {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
  padding: 0 var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: 1;
  text-decoration: none;
}

.files__download:hover {
  border-color: var(--border-strong);
  background: var(--surface-sunken);
}

.files__download--primary {
  border-color: transparent;
  background: var(--accent);
  color: var(--text-inverse);
}

.files__download--primary:hover {
  border-color: transparent;
  background: var(--accent);
  box-shadow: var(--shadow-md);
}
</style>
