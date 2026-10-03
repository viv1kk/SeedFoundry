<script setup lang="ts">
import ScreenPlaceholder from '../components/ScreenPlaceholder.vue'

defineProps<{ iteration: string }>()
</script>

<template>
  <ScreenPlaceholder :title="`Build, iteration ${iteration}`" note="The phase stepper and console arrive in M6." />
</template>
