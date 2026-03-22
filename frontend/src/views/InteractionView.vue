<template>
  <div class="main-view">
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">
          <span class="brand-diamond">&loz;</span>
          PARITY SWARM
        </div>
      </div>
      <div class="header-center">
        <div class="view-switcher">
          <button
            v-for="mode in ['graph', 'split', 'workbench']"
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: 'Graph', split: 'Split', workbench: 'Workbench' }[mode] }}
          </button>
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
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="5"
          :isSimulating="false"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>
      <div class="panel-wrapper right" :style="rightPanelStyle">
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
import GraphPanel from '../components/GraphPanel.vue'
import Step5Interaction from '../components/Step5Interaction.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation } from '../api/simulation'
import { getReport } from '../api/report'

const route = useRoute()
const router = useRouter()
const props = defineProps({ reportId: String })

const viewMode = ref('workbench')
const currentReportId = ref(route.params.reportId)
const simulationId = ref(null)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('ready')

const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

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
const toggleMaximize = (target) => { viewMode.value = viewMode.value === target ? 'split' : target }

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
            if (projRes.data.graph_id) await loadGraph(projRes.data.graph_id)
          }
        }
      }
    } else addLog(`Failed to get report: ${reportRes.error || 'Unknown'}`)
  } catch (err) { addLog(`Load error: ${err.message}`) }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  try {
    const res = await getGraphData(graphId)
    if (res.success) { graphData.value = res.data; addLog('Graph data loaded') }
  } catch (err) { addLog(`Graph load failed: ${err.message}`) }
  finally { graphLoading.value = false }
}

const refreshGraph = () => { if (projectData.value?.graph_id) loadGraph(projectData.value.graph_id) }

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
  position: relative;
}

.header-center { position: absolute; left: 50%; transform: translateX(-50%); }

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

.view-switcher {
  display: flex;
  background: var(--bg-base);
  padding: 2px;
  gap: 2px;
  border: 1px solid var(--border);
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 4px 14px;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.5px;
}

.switch-btn.active { background: var(--bg-elevated); color: var(--text-primary); }

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

.content-area { flex: 1; display: flex; position: relative; overflow: hidden; }

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left { border-right: 1px solid var(--border); }
</style>
