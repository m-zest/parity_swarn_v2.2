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
          <span class="step-num">Step 2/5</span>
          <span class="step-name">Environment Setup</span>
        </div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <main class="content-area">
      <div class="panel-wrapper left" style="width: 40%">
        <GraphPanel
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="2"
          @refresh="refreshGraph"
        />
      </div>
      <div class="panel-wrapper right" style="width: 60%">
        <Step2EnvSetup
          :simulationId="currentSimulationId"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, stopSimulation, getEnvStatus, closeSimulationEnv } from '../api/simulation'

const route = useRoute()
const router = useRouter()

const props = defineProps({ simulationId: String })

const currentSimulationId = ref(route.params.simulationId)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing')

const statusClass = computed(() => currentStatus.value)
const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Ready'
  return 'Preparing'
})

const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 100) systemLogs.value.shift()
}

const updateStatus = (status) => { currentStatus.value = status }

const handleGoBack = () => {
  if (projectData.value?.project_id) router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
  else router.push('/')
}

const handleNextStep = (params = {}) => {
  addLog('Entering Step 3: Run Simulation')
  if (params.maxRounds) addLog(`Custom simulation rounds: ${params.maxRounds}`)
  else addLog('Using auto-configured simulation rounds')
  const routeParams = { name: 'SimulationRun', params: { simulationId: currentSimulationId.value } }
  if (params.maxRounds) routeParams.query = { maxRounds: params.maxRounds }
  router.push(routeParams)
}

const checkAndStopRunningSimulation = async () => {
  if (!currentSimulationId.value) return
  try {
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog('Detected running simulation environment, shutting down...')
      try {
        const closeRes = await closeSimulationEnv({ simulation_id: currentSimulationId.value, timeout: 10 })
        if (closeRes.success) addLog('Simulation environment closed')
        else { addLog(`Failed to close: ${closeRes.error || 'Unknown'}`); await forceStopSimulation() }
      } catch (closeErr) { addLog(`Close error: ${closeErr.message}`); await forceStopSimulation() }
    } else {
      const simRes = await getSimulation(currentSimulationId.value)
      if (simRes.success && simRes.data?.status === 'running') {
        addLog('Detected simulation running, stopping...')
        await forceStopSimulation()
      }
    }
  } catch (err) { console.warn('Failed to check simulation status:', err) }
}

const forceStopSimulation = async () => {
  try {
    const stopRes = await stopSimulation({ simulation_id: currentSimulationId.value })
    if (stopRes.success) addLog('Simulation force stopped')
    else addLog(`Failed to force stop: ${stopRes.error || 'Unknown'}`)
  } catch (err) { addLog(`Force stop error: ${err.message}`) }
}

const loadSimulationData = async () => {
  try {
    addLog(`Loading simulation data: ${currentSimulationId.value}`)
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      if (simRes.data.project_id) {
        const projRes = await getProject(simRes.data.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(`Project loaded: ${projRes.data.project_id}`)
          if (projRes.data.graph_id) await loadGraph(projRes.data.graph_id)
        }
      }
    } else addLog(`Failed to load simulation: ${simRes.error || 'Unknown'}`)
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

onMounted(async () => {
  addLog('SimulationView initialized')
  await checkAndStopRunningSimulation()
  loadSimulationData()
})
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

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.step-num { font-weight: 700; color: var(--text-muted); }
.step-name { font-weight: 700; color: var(--text-primary); }

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--text-secondary);
}

.dot { width: 6px; height: 6px; background: var(--border-hover); }
.status-indicator.processing .dot { background: var(--red); animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: var(--green); }
.status-indicator.error .dot { background: var(--red); }

@keyframes pulse { 50% { opacity: 0.4; } }

.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left { border-right: 1px solid var(--border); }
</style>
