<template>
  <div class="launch-page">
    <header class="page-header">
      <span class="header-title">SIMULATION LAUNCHER</span>
    </header>

    <div class="page-body">
      <div class="launch-grid">
        <!-- Left: Configuration -->
        <div class="config-col">
          <!-- File upload -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">01 // SCENARIO CONTEXT</span>
            </div>
            <div class="card-body">
              <div
                class="drop-zone"
                :class="{ 'drag-active': isDragOver, 'has-files': files.length > 0 }"
                @dragover.prevent="isDragOver = true"
                @dragleave.prevent="isDragOver = false"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept=".pdf,.md,.txt"
                  @change="handleFileSelect"
                  style="display: none"
                  :disabled="loading"
                />
                <div v-if="files.length === 0" class="drop-placeholder">
                  <div class="drop-icon">[+]</div>
                  <div class="drop-text">Drop files or click to upload</div>
                  <div class="drop-hint">PDF / MD / TXT</div>
                </div>
                <div v-else class="file-list">
                  <div v-for="(file, i) in files" :key="i" class="file-row">
                    <span class="file-name">> {{ file.name }}</span>
                    <button @click.stop="removeFile(i)" class="file-remove">x</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Scenario selector -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">02 // ATTACK SCENARIO</span>
            </div>
            <div class="card-body">
              <select
                v-model="selectedScenarioId"
                class="field-select"
                @change="onScenarioSelect"
                :disabled="loading"
              >
                <option value="">-- select preset scenario --</option>
                <option v-for="s in attackScenarios" :key="s.id" :value="s.id">
                  {{ s.name }}
                </option>
              </select>
            </div>
          </div>

          <!-- Prompt -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">03 // SIMULATION PROMPT</span>
            </div>
            <div class="card-body">
              <textarea
                v-model="formData.simulationRequirement"
                class="field-textarea"
                placeholder="// select a scenario above or enter custom requirements..."
                rows="6"
                :disabled="loading"
              ></textarea>
            </div>
          </div>

          <!-- Execute button -->
          <button
            class="execute-btn"
            @click="startSimulation"
            :disabled="!canSubmit || loading"
          >
            <span v-if="!loading">EXECUTE</span>
            <span v-else>INITIALIZING...</span>
            <span class="btn-arrow">>></span>
          </button>
        </div>

        <!-- Right: Terminal output -->
        <div class="terminal-col">
          <div class="card terminal-card">
            <div class="card-header">
              <span class="card-title">LIVE OUTPUT</span>
              <span class="terminal-status">
                <span class="pulse-dot"></span>
                MONITORING
              </span>
            </div>
            <div class="terminal-body" ref="terminalBody">
              <div v-for="(line, i) in terminalLogs" :key="i" class="term-line">
                <span class="term-ts">{{ line.time }}</span>
                <span class="term-msg" :class="line.type">{{ line.msg }}</span>
              </div>
              <div v-if="terminalLogs.length === 0" class="term-empty">
                <span class="term-cursor">_</span> awaiting simulation output...
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const attackScenarios = [
  { id: 'direct_attacker', name: 'Direct Attacker -- API Key Theft', category: 'direct', difficulty: 'Easy' },
  { id: 'patient_planner', name: 'Patient Planner -- Backdoor Insertion', category: 'subtle', difficulty: 'Hard' },
  { id: 'social_engineer', name: 'Social Engineer -- Info Extraction', category: 'social', difficulty: 'Hard' },
  { id: 'distraction_agent', name: 'Distraction Agent -- Log Tampering', category: 'direct', difficulty: 'Medium' },
  { id: 'steganographic_agent', name: 'Steganographic Agent -- Data Hiding', category: 'steganographic', difficulty: 'Hard' },
  { id: 'incremental_thief', name: 'Incremental Thief -- PII Exfiltration', category: 'subtle', difficulty: 'Hard' },
  { id: 'colluding_pair', name: 'Colluding Pair -- Credential Theft', category: 'social', difficulty: 'Hard' },
  { id: 'context_manipulator', name: 'Context Manipulator -- Prompt Injection', category: 'subtle', difficulty: 'Medium' },
  { id: 'resource_abuser', name: 'Resource Abuser -- Compute Theft', category: 'direct', difficulty: 'Medium' },
  { id: 'alignment_faker', name: 'Alignment Faker -- Sandbagging', category: 'steganographic', difficulty: 'Hard' },
]

const selectedScenarioId = ref('')
const formData = ref({ simulationRequirement: '' })
const files = ref([])
const loading = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)
const terminalBody = ref(null)
const terminalLogs = ref([])
let terminalTimer = null

const canSubmit = computed(() => formData.value.simulationRequirement.trim() !== '' && files.value.length > 0)

const onScenarioSelect = () => {
  const scenario = attackScenarios.find(s => s.id === selectedScenarioId.value)
  if (scenario) {
    formData.value.simulationRequirement = `Run the "${scenario.name}" attack scenario.\n\nCategory: ${scenario.category}\nDifficulty: ${scenario.difficulty}\nScenario ID: ${scenario.id}`
  }
}

const triggerFileInput = () => { if (!loading.value) fileInput.value?.click() }
const handleFileSelect = (event) => addFiles(Array.from(event.target.files))
const handleDrop = (e) => { isDragOver.value = false; if (!loading.value) addFiles(Array.from(e.dataTransfer.files)) }

const addFiles = (newFiles) => {
  files.value.push(...newFiles.filter(f => ['pdf','md','txt'].includes(f.name.split('.').pop().toLowerCase())))
}

const removeFile = (index) => { files.value.splice(index, 1) }

const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, formData.value.simulationRequirement)
    router.push({ name: 'Process', params: { projectId: 'new' } })
  })
}

const addLog = (msg, type = 'info') => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false })
  terminalLogs.value.push({ time, msg, type })
  if (terminalLogs.value.length > 200) terminalLogs.value = terminalLogs.value.slice(-200)
  nextTick(() => { if (terminalBody.value) terminalBody.value.scrollTop = terminalBody.value.scrollHeight })
}

const fetchTerminalLogs = async () => {
  try {
    const res = await fetch('http://localhost:5001/api/simulation/logs')
    if (res.ok) {
      const data = await res.json()
      if (data.data?.logs) {
        data.data.logs.forEach(log => addLog(log))
      }
    }
  } catch (e) { /* backend not running */ }
}

onMounted(() => {
  addLog('Parity Swarm v2.2 initialized.', 'success')
  addLog('Awaiting scenario configuration...', 'info')
  terminalTimer = setInterval(fetchTerminalLogs, 5000)
})

onUnmounted(() => { if (terminalTimer) clearInterval(terminalTimer) })
</script>

<style scoped>
.launch-page {
  min-height: 100vh;
}

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

.page-body {
  padding: 20px;
}

.launch-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-items: start;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  overflow: hidden;
  margin-bottom: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--text-secondary);
}

.card-body {
  padding: 16px;
}

/* Drop zone */
.drop-zone {
  border: 1px dashed var(--border-hover);
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  background: var(--bg-base);
}

.drop-zone:hover,
.drop-zone.drag-active {
  border-color: var(--red);
  background: var(--red-dim);
}

.drop-zone.has-files {
  align-items: flex-start;
}

.drop-placeholder {
  text-align: center;
  padding: 20px;
}

.drop-icon {
  font-size: 20px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.drop-text {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.drop-hint {
  font-size: 9px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.file-list {
  width: 100%;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--bg-elevated);
  font-size: 11px;
}

.file-name {
  color: var(--green);
}

.file-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  padding: 0 4px;
}

.file-remove:hover {
  color: var(--red);
}

/* Fields */
.field-select {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-base);
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-size: 11px;
  outline: none;
  cursor: pointer;
  appearance: none;
}

.field-select:focus {
  border-color: var(--red);
}

.field-textarea {
  width: 100%;
  padding: 12px;
  background: var(--bg-base);
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-size: 11px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  min-height: 120px;
}

.field-textarea:focus {
  border-color: var(--red);
}

.field-textarea::placeholder {
  color: var(--text-muted);
}

/* Execute button */
.execute-btn {
  width: 100%;
  background: var(--red);
  color: #fff;
  border: none;
  padding: 14px;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 2px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background 0.15s;
}

.execute-btn:hover:not(:disabled) {
  background: #dc2626;
}

.execute-btn:disabled {
  background: var(--border);
  color: var(--text-muted);
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 14px;
}

/* Terminal */
.terminal-card {
  position: sticky;
  top: 64px;
}

.terminal-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  color: var(--terminal-green);
  letter-spacing: 1px;
}

.pulse-dot {
  width: 5px;
  height: 5px;
  background: var(--terminal-green);
  animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.terminal-body {
  background: #050505;
  padding: 16px;
  min-height: 400px;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
}

.term-line {
  display: flex;
  gap: 12px;
  font-size: 10px;
  line-height: 1.8;
}

.term-ts {
  color: #333;
  min-width: 65px;
  flex-shrink: 0;
}

.term-msg {
  color: var(--terminal-green);
  word-break: break-all;
}

.term-msg.error { color: var(--red); }
.term-msg.success { color: var(--terminal-green); }
.term-msg.info { color: #666; }

.term-empty {
  color: #333;
  font-size: 11px;
}

.term-cursor {
  color: var(--terminal-green);
  animation: cursor-blink 1s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

@media (max-width: 1000px) {
  .launch-grid {
    grid-template-columns: 1fr;
  }
}
</style>
