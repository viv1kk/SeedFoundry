<script setup lang="ts">
// A yes-or-no question in a modal: delete a file, replace a core file. Cancel comes first in
// the tab order, so Enter on open does not confirm by accident.
import BaseButton from './BaseButton.vue'
import BaseModal from './BaseModal.vue'

withDefaults(defineProps<{ open: boolean; title: string; confirmLabel: string; busy?: boolean; error?: string | null }>(), {
  busy: false,
  error: null,
})
const emit = defineEmits<{ confirm: []; cancel: [] }>()
</script>

<template>
  <BaseModal :open="open" :title="title" @close="emit('cancel')">
    <div class="confirm__body" data-test="confirm-body"><slot /></div>
    <p v-if="error" class="confirm__error" role="alert">{{ error }}</p>
    <template #footer>
      <BaseButton data-test="confirm-cancel" @click="emit('cancel')">Cancel</BaseButton>
      <BaseButton variant="primary" :disabled="busy" data-test="confirm-ok" @click="emit('confirm')">{{ confirmLabel }}</BaseButton>
    </template>
  </BaseModal>
</template>

<style scoped>
.confirm__body {
  display: grid;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.confirm__error {
  margin-top: var(--space-3);
  color: var(--status-negative);
  font-size: var(--text-sm);
}
</style>
