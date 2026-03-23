<template>
  <div class="history-page">
    <header class="page-header">
      <span class="header-title">SIMULATION HISTORY</span>
    </header>
    <div class="page-body">
      <HistoryDatabase />
    </div>
  </div>
</template>

<script setup>
import HistoryDatabase from '../components/HistoryDatabase.vue'
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
