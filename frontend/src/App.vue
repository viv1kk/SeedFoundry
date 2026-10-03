<script setup lang="ts">
// The app shell (ui-spec.md section 1): the top bar over the current screen.
import TopBar from './components/shell/TopBar.vue'
</script>

<template>
  <div class="shell">
    <TopBar />
    <main class="screen">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.shell {
  --top-bar-height: 52px;
}

.screen {
  min-height: calc(100vh - var(--top-bar-height));
}
</style>
