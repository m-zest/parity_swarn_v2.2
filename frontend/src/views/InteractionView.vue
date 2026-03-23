<template>
  <div class="main-view">
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">
          <span class="brand-diamond">&loz;</span>
          PARITY SWARM
        </div>
      </div>
      <div class="header-right">
        <div class="workflow-step">
          <span class="step-num">Step 5/5</span>
          <span class="step-name">Deep Interaction</span>
        </div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <main class="content-area">
      <div class="panel-wrapper full">
        <Step5Interaction
          :reportId="currentReportId"
          :simulationId="simulationId"
          :systemLogs="systemLogs"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Step5Interaction from '../components/Step5Interaction.vue'
import { getProject } from '../api/graph'
import { getSimulation } from '../api/simulation'
import { getReport } from '../api/report'

const route = useRoute()
const router = useRouter()
const props = defineProps({ reportId: String })

const currentReportId = ref(route.params.reportId)
const simulationId = ref(null)
const projectData = ref(null)
const systemLogs = ref([])
const currentStatus = ref('ready')

const statusClass = computed(() => currentStatus.value)
const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  if (currentStatus.value === 'processing') return 'Processing'
  return 'Ready'
})

const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) systemLogs.value.shift()
}

const updateStatus = (status) => { currentStatus.value = status }

const loadReportData = async () => {
  try {
    addLog(`Loading report data: ${currentReportId.value}`)
    const reportRes = await getReport(currentReportId.value)
    if (reportRes.success && reportRes.data) {
      simulationId.value = reportRes.data.simulation_id
      if (simulationId.value) {
        const simRes = await getSimulation(simulationId.value)
        if (simRes.success && simRes.data?.project_id) {
          const projRes = await getProject(simRes.data.project_id)
          if (projRes.success && projRes.data) {
            projectData.value = projRes.data
            addLog(`Project loaded: ${projRes.data.project_id}`)
          }
        }
      }
    } else addLog(`Failed to get report: ${reportRes.error || 'Unknown'}`)
  } catch (err) { addLog(`Load error: ${err.message}`) }
}

watch(() => route.params.reportId, (newId) => {
  if (newId && newId !== currentReportId.value) { currentReportId.value = newId; loadReportData() }
}, { immediate: true })

onMounted(() => { addLog('InteractionView initialized'); loadReportData() })
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
  overflow: hidden;
}

.app-header {
  height: 44px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--bg-card);
  z-index: 100;
}

.brand {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  cursor: pointer;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-diamond { color: var(--red); font-size: 14px; }

.header-right { display: flex; align-items: center; gap: 16px; }
.workflow-step { display: flex; align-items: center; gap: 8px; font-size: 11px; }
.step-num { font-weight: 700; color: var(--text-muted); }
.step-name { font-weight: 700; color: var(--text-primary); }

.status-indicator { display: flex; align-items: center; gap: 6px; font-size: 10px; color: var(--text-secondary); }
.dot { width: 6px; height: 6px; background: var(--border-hover); }
.status-indicator.ready .dot { background: var(--green); }
.status-indicator.processing .dot { background: var(--orange); animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: var(--green); }
.status-indicator.error .dot { background: var(--red); }

@keyframes pulse { 50% { opacity: 0.4; } }

.content-area { flex: 1; display: flex; overflow: hidden; }

.panel-wrapper.full {
  width: 100%;
  height: 100%;
  overflow: hidden;
}
</style>
