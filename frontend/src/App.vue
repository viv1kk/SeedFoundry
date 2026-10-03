<script setup lang="ts">
// The app shell (ui-spec.md section 1): the top bar over the current screen, the rebuild modal
// (ui-spec.md section 6), which iteration 1's report opens over any page, and the hidden demo
// controller (ui-spec.md section 8), whose shortcuts work on every screen.
import RebuildModal from './components/rebuild/RebuildModal.vue'
import TopBar from './components/shell/TopBar.vue'
import DemoController from './demo/DemoController.vue'
</script>

<template>
  <div class="shell">
    <TopBar />
    <main class="screen">
      <RouterView />
    </main>
    <RebuildModal />
    <DemoController />
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
