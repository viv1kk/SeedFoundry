<script setup lang="ts">
import ScreenPlaceholder from '../components/ScreenPlaceholder.vue'

defineProps<{ iteration: string }>()
</script>

<template>
  <ScreenPlaceholder :title="`Review, iteration ${iteration}`" note="The build report arrives in M9, the dashboard in M7." />
</template>
