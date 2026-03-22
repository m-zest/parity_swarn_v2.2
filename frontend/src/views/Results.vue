<template>
  <div class="results-page">
    <header class="page-header">
      <span class="header-title">SIMULATION RESULTS</span>
      <span class="header-count" v-if="simulations.length">{{ simulations.length }} records</span>
    </header>

    <div class="page-body">
      <!-- Loading state -->
      <div v-if="loading" class="loading-state">
        <span class="loading-text">FETCHING RECORDS...</span>
      </div>

      <!-- Empty state -->
      <div v-else-if="simulations.length === 0" class="empty-state">
        <div class="empty-icon">[--]</div>
        <div class="empty-text">No simulation records found</div>
        <div class="empty-hint">Launch a simulation to see results here</div>
      </div>

      <!-- Results table -->
      <div v-else class="results-table">
        <div class="table-header">
          <span class="col col-id">ID</span>
          <span class="col col-project">PROJECT</span>
          <span class="col col-status">STATUS</span>
          <span class="col col-date">DATE</span>
          <span class="col col-actions">ACTIONS</span>
        </div>
        <div
          v-for="sim in simulations"
          :key="sim.simulation_id || sim.id"
          class="table-row"
          @click="navigateToSim(sim)"
        >
          <span class="col col-id">
            <span class="id-hash">#</span>{{ (sim.simulation_id || sim.id || '').slice(0, 8) }}
          </span>
          <span class="col col-project">
            <span class="project-name">{{ sim.project_name || sim.project_id?.slice(0, 12) || '--' }}</span>
          </span>
          <span class="col col-status">
            <span class="status-tag" :class="statusClass(sim.status)">{{ sim.status || 'unknown' }}</span>
          </span>
          <span class="col col-date">
            {{ formatDate(sim.created_at) }}
          </span>
          <span class="col col-actions">
            <button class="action-btn" @click.stop="navigateToSim(sim)">VIEW >></button>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getSimulationHistory } from '../api/simulation'

const router = useRouter()
const simulations = ref([])
const loading = ref(true)

const fetchResults = async () => {
  loading.value = true
  try {
    const res = await getSimulationHistory(50)
    if (res.success && res.data) {
      simulations.value = Array.isArray(res.data) ? res.data : res.data.simulations || []
    }
  } catch (e) {
    console.error('Failed to fetch results:', e)
  } finally {
    loading.value = false
  }
}

const statusClass = (status) => {
  if (!status) return ''
  if (status === 'completed') return 'tag-green'
  if (status === 'running' || status === 'preparing') return 'tag-orange'
  if (status === 'failed') return 'tag-red'
  return ''
}

const formatDate = (dateStr) => {
  if (!dateStr) return '--'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' +
           d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
  } catch { return dateStr }
}

const navigateToSim = (sim) => {
  const id = sim.simulation_id || sim.id
  if (id) {
    if (sim.report_id) {
      router.push({ name: 'Report', params: { reportId: sim.report_id } })
    } else {
      router.push({ name: 'Simulation', params: { simulationId: id } })
    }
  }
}

onMounted(fetchResults)
</script>

<style scoped>
.results-page {
  min-height: 100vh;
}

.page-header {
  height: 44px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
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

.header-count {
  font-size: 9px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.page-body {
  padding: 20px;
}

/* States */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--text-muted);
}

.loading-text {
  font-size: 10px;
  letter-spacing: 2px;
  animation: blink 1.5s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.empty-icon {
  font-size: 24px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.empty-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 10px;
  color: var(--text-muted);
}

/* Table */
.results-table {
  background: var(--bg-card);
  border: 1px solid var(--border);
}

.table-header {
  display: flex;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-elevated);
}

.table-header .col {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: var(--text-muted);
}

.table-row {
  display: flex;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.1s;
}

.table-row:hover {
  background: var(--bg-elevated);
}

.table-row:last-child {
  border-bottom: none;
}

.col {
  font-size: 11px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
}

.col-id { width: 120px; flex-shrink: 0; }
.col-project { flex: 1; }
.col-status { width: 120px; flex-shrink: 0; }
.col-date { width: 140px; flex-shrink: 0; }
.col-actions { width: 100px; flex-shrink: 0; justify-content: flex-end; }

.id-hash {
  color: var(--text-muted);
  margin-right: 2px;
}

.project-name {
  color: var(--text-primary);
}

.status-tag {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 1px;
  padding: 2px 8px;
  border: 1px solid var(--border);
  text-transform: uppercase;
}

.status-tag.tag-green {
  color: var(--green);
  border-color: var(--green-border);
  background: var(--green-dim);
}

.status-tag.tag-orange {
  color: var(--orange);
  border-color: var(--orange-border);
  background: var(--orange-dim);
}

.status-tag.tag-red {
  color: var(--red);
  border-color: var(--red-border);
  background: var(--red-dim);
}

.action-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 9px;
  letter-spacing: 1px;
  padding: 4px 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:hover {
  border-color: var(--red);
  color: var(--red);
}
</style>
