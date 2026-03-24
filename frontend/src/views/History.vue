<template>
  <div class="history-page">
    <header class="page-header">
      <span class="header-title">SIMULATION HISTORY</span>
    </header>
    <div class="page-body">
      <GpuFallback v-if="backendOffline" />
      <HistoryDatabase v-else />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import GpuFallback from '../components/GpuFallback.vue'

const backendOffline = ref(false)

onMounted(async () => {
  try {
    await fetch('/api/health', { signal: AbortSignal.timeout(3000) })
  } catch {
    backendOffline.value = true
  }
})
</script>

<style scoped>
.history-page { min-height: 100vh; }

.page-header {
  height: 44px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-title {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--text-secondary);
}

.page-body { padding: 20px; }
</style>
