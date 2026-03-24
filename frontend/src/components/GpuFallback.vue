<template>
  <div class="fallback-overlay">
    <div class="fallback-card">
      <div class="fallback-border"></div>
      <div class="fallback-content">
        <div class="fallback-title">LIVE SIMULATION REQUIRES GPU BACKEND</div>
        <div class="fallback-body">
          <p>This page requires the simulation backend running on a dedicated GPU server (Lambda Labs A100).</p>
          <div class="fallback-hints">
            <span class="hint-arrow">&rarr;</span> View completed results on the Dashboard<br>
            <span class="hint-arrow">&rarr;</span> View the research paper for full analysis
          </div>
        </div>
        <div class="fallback-actions">
          <router-link to="/" class="fallback-btn btn-primary">&larr; Go to Dashboard</router-link>
          <a
            href="https://apartresearch.com/project/parity-swarm-using-populationbased-social-simulation-to-discover-ai-safety-monitor-blind-spots-c9qc"
            target="_blank"
            rel="noopener noreferrer"
            class="fallback-btn btn-secondary"
          >[P] Read Paper</a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fallback-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: 40px 20px;
}

.fallback-card {
  background: #0f0f0f;
  border: 1px solid #f97316;
  max-width: 560px;
  width: 100%;
  position: relative;
}

.fallback-border {
  height: 2px;
  background: #f97316;
}

.fallback-content {
  padding: 32px;
}

.fallback-title {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #f97316;
  margin-bottom: 20px;
  font-family: 'Courier New', Consolas, monospace;
}

.fallback-body p {
  font-size: 11px;
  line-height: 1.7;
  color: #999;
  margin: 0 0 16px 0;
  font-family: 'Courier New', Consolas, monospace;
}

.fallback-hints {
  font-size: 11px;
  line-height: 2;
  color: #ccc;
  margin-bottom: 24px;
  font-family: 'Courier New', Consolas, monospace;
}

.hint-arrow {
  color: #f97316;
}

.fallback-actions {
  display: flex;
  gap: 12px;
}

.fallback-btn {
  padding: 8px 16px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  text-decoration: none;
  font-family: 'Courier New', Consolas, monospace;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.btn-primary {
  background: #f97316;
  color: #000;
  border: 1px solid #f97316;
}

.btn-primary:hover {
  background: #fb923c;
}

.btn-secondary {
  background: transparent;
  color: #999;
  border: 1px solid #333;
}

.btn-secondary:hover {
  border-color: #666;
  color: #ccc;
}
</style>
