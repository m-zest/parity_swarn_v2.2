<template>
  <div class="terminal-page">
    <header class="page-header">
      <div class="header-left">
        <span class="header-title">LIVE TERMINAL</span>
      </div>
      <div class="header-right">
        <span class="log-count">{{ logs.length }} lines</span>
        <button class="clear-btn" @click="clearLogs">CLEAR</button>
        <span class="terminal-indicator">
          <span class="pulse-dot"></span>
          CONNECTED
        </span>
      </div>
    </header>

    <GpuFallback v-if="backendOffline" />

    <div v-else class="terminal-body" ref="terminalBody">
      <div class="terminal-content">
        <div v-for="(line, i) in logs" :key="i" class="log-line">
          <span class="line-num">{{ String(i + 1).padStart(4, '0') }}</span>
          <span class="line-ts">{{ line.time }}</span>
          <span class="line-msg" :class="line.type">{{ line.msg }}</span>
        </div>
        <div v-if="logs.length === 0" class="terminal-idle">
          <div class="idle-line">> Parity Swarm v2.2 Terminal</div>
          <div class="idle-line">> Monitoring backend at localhost:5001</div>
          <div class="idle-line">> Polling interval: 3s</div>
          <div class="idle-line">></div>
          <div class="idle-line">> Waiting for activity...<span class="cursor">_</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import GpuFallback from '../components/GpuFallback.vue'

const logs = ref([])
const terminalBody = ref(null)
const backendOffline = ref(false)
let pollTimer = null

const addLog = (msg, type = 'info') => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false })
  logs.value.push({ time, msg, type })
  if (logs.value.length > 1000) logs.value = logs.value.slice(-1000)
  nextTick(() => {
    if (terminalBody.value) terminalBody.value.scrollTop = terminalBody.value.scrollHeight
  })
}

const clearLogs = () => {
  logs.value = []
  addLog('Terminal cleared.', 'info')
}

const fetchLogs = async () => {
  try {
    const res = await fetch('http://localhost:5001/api/simulation/logs')
    if (res.ok) {
      const data = await res.json()
      if (data.data?.logs) {
        data.data.logs.forEach(log => {
          const type = log.toLowerCase().includes('error') ? 'error'
            : log.toLowerCase().includes('alert') ? 'error'
            : log.toLowerCase().includes('completed') ? 'success'
            : log.toLowerCase().includes('started') ? 'success'
            : 'info'
          addLog(log, type)
        })
      }
    }
  } catch (e) { /* backend offline */ }
}

onMounted(async () => {
  try {
    await fetch('/api/health', { signal: AbortSignal.timeout(3000) })
  } catch {
    backendOffline.value = true
    return
  }
  addLog('Parity Swarm v2.2 terminal initialized.', 'success')
  addLog('Connecting to backend...', 'info')
  fetchLogs()
  pollTimer = setInterval(fetchLogs, 3000)
})

onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<style scoped>
.terminal-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #050505;
}

.page-header {
  height: 44px;
  background: #0a0a0a;
  border-bottom: 1px solid #1a1a1a;
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

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.log-count {
  font-size: 9px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.clear-btn {
  background: none;
  border: 1px solid #2a2a2a;
  color: var(--text-muted);
  font-size: 9px;
  letter-spacing: 1px;
  padding: 3px 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.clear-btn:hover {
  border-color: var(--red);
  color: var(--red);
}

.terminal-indicator {
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
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.terminal-content {
  min-height: calc(100vh - 76px);
}

.log-line {
  display: flex;
  gap: 12px;
  font-size: 11px;
  line-height: 1.8;
}

.line-num {
  color: #2a2a2a;
  min-width: 35px;
  flex-shrink: 0;
  text-align: right;
  user-select: none;
}

.line-ts {
  color: #333;
  min-width: 65px;
  flex-shrink: 0;
}

.line-msg {
  color: #888;
  word-break: break-all;
}

.line-msg.success { color: var(--terminal-green); }
.line-msg.error { color: var(--red); }
.line-msg.info { color: #666; }

.terminal-idle {
  font-size: 12px;
  line-height: 2;
  color: #444;
}

.idle-line {
  margin-left: 4px;
}

.cursor {
  color: var(--terminal-green);
  animation: cursor-blink 1s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
