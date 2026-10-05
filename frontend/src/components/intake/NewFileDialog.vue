<script setup lang="ts">
// New file (FR-IN-6): a category, one of the four initiation files (D-84). The name is the
// category's own (Environment_01.md for Environment.md, D-85), shown and not typed: it follows
// the category. A taken core slot asks "Replace it?" in the same dialog, naming the file it
// replaces (FR-IN-3); the server's 409 core_slot_taken is the backstop (D-35).
import { computed, ref, useId, watch } from 'vue'
import { ApiError, messageOf } from '../../api'
import { useIntakeStore } from '../../stores/intake'
import BaseButton from '../base/BaseButton.vue'
import BaseModal from '../base/BaseModal.vue'

const props = defineProps<{ open: boolean; initialCategory: string | null }>()
const emit = defineEmits<{ close: []; created: [id: string] }>()

const intake = useIntakeStore()
const categoryId = useId()

const name = ref('')
const category = ref('')
const error = ref<string | null>(null)
const busy = ref(false)
const confirming = ref<{ holder: string; message: string } | null>(null)

/** The first core slot without a file, else the first category. */
function firstOpenCategory(): string {
  return intake.coreCategories.find((c) => !intake.slotHolder(c.id))?.id ?? intake.defaultCategory
}

watch(
  () => props.open,
  (open) => {
    if (!open) return
    category.value = props.initialCategory ?? firstOpenCategory()
    name.value = intake.suggestedName(category.value)
    error.value = null
    confirming.value = null
  },
  { immediate: true },
)

watch(category, (value) => {
  name.value = intake.suggestedName(value)
  error.value = null
})

const holder = computed(() => intake.slotHolder(category.value))
const canCreate = computed(() => name.value.trim() !== '' && category.value !== '' && !busy.value)

async function create(replace: boolean): Promise<void> {
  if (!canCreate.value) return
  if (holder.value && !replace) {
    confirming.value = {
      holder: holder.value.name,
      message: `${intake.labelOf(category.value)} already has ${holder.value.name}. Replace it with ${name.value.trim()}?`,
    }
    return
  }
  busy.value = true
  error.value = null
  try {
    const file = await intake.create(name.value, category.value, replace)
    emit('created', file.id)
    emit('close')
  } catch (failure) {
    if (failure instanceof ApiError && failure.code === 'core_slot_taken') {
      const existing = (failure.detail.existing as { name?: string } | undefined)?.name ?? ''
      confirming.value = { holder: existing, message: failure.message }
    } else {
      confirming.value = null
      error.value = messageOf(failure)
    }
  } finally {
    busy.value = false
  }
}

function onSubmit(): void {
  void create(confirming.value !== null)
}
</script>

<template>
  <BaseModal :open="open" :title="confirming ? 'Replace it?' : 'New file'" @close="emit('close')">
    <form id="new-file-form" class="form" data-test="new-file-dialog" @submit.prevent="onSubmit">
      <template v-if="!confirming">
        <div class="form__field">
          <label :for="categoryId" class="form__label">Category</label>
          <select :id="categoryId" v-model="category" class="form__input" data-test="new-category">
            <option v-for="c in intake.categories" :key="c.id" :value="c.id">{{ c.label }}</option>
          </select>
          <p v-if="holder" class="form__warning" data-test="new-replace-warning">Replaces existing {{ holder.name }}</p>
        </div>
        <p class="form__name">Name <span class="form__mono" data-test="new-name">{{ name }}</span></p>
      </template>
      <div v-else class="form__confirm" data-test="new-confirm">
        <p>{{ confirming.message }}</p>
        <p>{{ confirming.holder }} will be deleted.</p>
      </div>
      <p v-if="error" class="form__error" role="alert" data-test="new-error">{{ error }}</p>
    </form>
    <template #footer>
      <BaseButton v-if="confirming" data-test="new-back" @click="confirming = null">Back</BaseButton>
      <BaseButton v-else data-test="new-cancel" @click="emit('close')">Cancel</BaseButton>
      <BaseButton variant="primary" type="submit" form="new-file-form" :disabled="!canCreate" data-test="new-create">
        {{ confirming ? `Replace ${confirming.holder}` : 'Create' }}
      </BaseButton>
    </template>
  </BaseModal>
</template>

<style scoped>
.form {
  display: grid;
  gap: var(--space-4);
}

.form__field {
  display: grid;
  gap: var(--space-1);
}

.form__label {
  font-size: var(--text-sm);
  font-weight: 600;
}

.form__input {
  min-height: 32px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  color: var(--text-primary);
  font: inherit;
  font-size: var(--text-sm);
}

.form__name {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.form__mono {
  margin-left: var(--space-2);
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.form__input[aria-invalid='true'] {
  border-color: var(--status-negative);
}

.form__warning {
  color: var(--status-warning);
  font-size: var(--text-sm);
  font-weight: 600;
}

.form__confirm {
  display: grid;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.form__error {
  color: var(--status-negative);
  font-size: var(--text-sm);
}
</style>
