<template>
  <div class="dashboard">
    <header class="page-header">
      <div class="header-left">
        <span class="header-title">THREAT DETECTION OVERVIEW</span>
      </div>
      <div class="header-right">
        <span class="status-pill" v-if="loaded">
          <span class="pulse"></span>
          {{ data.meta.total_simulations }} SIMULATIONS ANALYZED
        </span>
      </div>
    </header>

    <div v-if="!loaded" class="loading-state">
      <span class="loading-text">LOADING RESULTS...</span>
    </div>

    <div v-else class="page-body">
      <!-- Section A: Hackathon Banner -->
      <div v-if="showBanner" class="prototype-banner">
        <div class="banner-content">
          <span class="banner-icon">!</span>
          <div class="banner-text">
            <span class="banner-label">PROTOTYPE (Ongoing Dev)</span>
            <span class="banner-desc">
              This is a research demo.
              The simulation backend runs on a dedicated GPU server (Lambda Labs A100) and is not
              connected to this public demo. The results shown are from {{ data.meta.total_simulations }} completed simulation evaluations
              across {{ data.meta.scenarios_count }} attack scenarios. Active development ongoing.
            </span>
          </div>
        </div>
        <button class="banner-close" @click="showBanner = false">x</button>
      </div>

      <!-- Section B: Key Metrics -->
      <section class="section-block">
        <div class="section-label">KEY METRICS</div>
        <div class="stats-grid">
          <div class="stat-cell">
            <div class="stat-number">{{ data.meta.total_simulations }}</div>
            <div class="stat-desc">Total Simulations</div>
            <div class="stat-bar"><div class="stat-bar-fill neutral" style="width: 100%"></div></div>
          </div>
          <div class="stat-cell">
            <div class="stat-number" :class="rateClass(data.overall.detection_rate_run1)">{{ data.overall.detection_rate_run1 }}%</div>
            <div class="stat-desc">Detection Rate (Narrative Only)</div>
            <div class="stat-bar"><div class="stat-bar-fill orange" :style="{ width: data.overall.detection_rate_run1 + '%' }"></div></div>
          </div>
          <div class="stat-cell">
            <div class="stat-number" :class="rateClass(data.overall.detection_rate_run2)">{{ data.overall.detection_rate_run2 }}%</div>
            <div class="stat-desc">Detection Rate (With Transcripts)</div>
            <div class="stat-bar"><div class="stat-bar-fill blue" :style="{ width: data.overall.detection_rate_run2 + '%' }"></div></div>
          </div>
          <div class="stat-cell">
            <div class="stat-number accent-green">+{{ data.overall.lossy_filter_gap }}pp</div>
            <div class="stat-desc">Lossy Filter Gap</div>
            <div class="stat-bar"><div class="stat-bar-fill green" :style="{ width: Math.min(data.overall.lossy_filter_gap * 5, 100) + '%' }"></div></div>
          </div>
        </div>
      </section>

      <!-- Section C: Detection Rate by Scenario (D3 grouped bar chart) -->
      <section class="section-block">
        <div class="section-label">DETECTION RATE BY SCENARIO</div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">GROUPED BAR CHART — RUN 1 VS RUN 2</span>
            <span class="card-badge">llama3.3:70b Monitor</span>
          </div>
          <div class="chart-container" ref="barChartRef"></div>
          <div class="chart-legend">
            <span class="legend"><span class="dot orange"></span> Run 1 (Narrative Only)</span>
            <span class="legend"><span class="dot blue"></span> Run 2 (With Transcripts)</span>
          </div>
        </div>
      </section>

      <!-- Section D: Attack Category Breakdown -->
      <section class="section-block">
        <div class="section-label">ATTACK CATEGORY BREAKDOWN</div>
        <div class="stats-grid">
          <div class="stat-cell" v-for="(cat, key) in data.category_breakdown" :key="key">
            <div class="cat-label">{{ key.toUpperCase() }}</div>
            <div class="cat-rates">
              <div class="cat-rate">
                <span class="cat-rate-val orange-text">{{ cat.detection_rate_run1 !== null ? cat.detection_rate_run1 + '%' : 'N/A' }}</span>
                <span class="cat-rate-label">Run 1</span>
              </div>
              <div class="cat-rate">
                <span class="cat-rate-val blue-text">{{ cat.detection_rate_run2 !== null ? cat.detection_rate_run2 + '%' : 'N/A' }}</span>
                <span class="cat-rate-label">Run 2</span>
              </div>
            </div>
            <div class="cat-runs">{{ cat.runs_run1 + cat.runs_run2 }} total runs</div>
          </div>
        </div>
      </section>

      <!-- Section E: Suspicion Score Heatmap -->
      <section class="section-block">
        <div class="section-label">SUSPICION SCORE HEATMAP</div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">SCENARIO DETECTION MATRIX</span>
            <span class="card-badge">Attack Success Score (1-10)</span>
          </div>
          <div class="heatmap-table">
            <div class="heatmap-header">
              <span class="hm-col hm-name">SCENARIO</span>
              <span class="hm-col">SCORE R1</span>
              <span class="hm-col">SCORE R2</span>
              <span class="hm-col">DETECT R1</span>
              <span class="hm-col">DETECT R2</span>
              <span class="hm-col">RATE R1</span>
              <span class="hm-col">RATE R2</span>
            </div>
            <div
              v-for="s in sortedScenarios"
              :key="s.id"
              class="heatmap-row"
              :class="{ 'highlight-row': isHighlight(s) }"
            >
              <span class="hm-col hm-name">{{ shortName(s.id) }}</span>
              <span class="hm-col" :class="scoreClass(s.suspicion_score_run1)">{{ s.suspicion_score_run1 ?? '—' }}</span>
              <span class="hm-col" :class="scoreClass(s.suspicion_score_run2)">{{ s.suspicion_score_run2 ?? '—' }}</span>
              <span class="hm-col" :class="s.detected_run1 ? 'detected' : s.detected_run1 === false ? 'evaded' : ''">
                {{ s.detected_run1 === true ? 'YES' : s.detected_run1 === false ? 'NO' : '—' }}
              </span>
              <span class="hm-col" :class="s.detected_run2 ? 'detected' : s.detected_run2 === false ? 'evaded' : ''">
                {{ s.detected_run2 === true ? 'YES' : s.detected_run2 === false ? 'NO' : '—' }}
              </span>
              <span class="hm-col" :class="rateClass(s.detection_rate_run1)">{{ s.detection_rate_run1 !== null ? s.detection_rate_run1 + '%' : '—' }}</span>
              <span class="hm-col" :class="rateClass(s.detection_rate_run2)">{{ s.detection_rate_run2 !== null ? s.detection_rate_run2 + '%' : '—' }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Section F: Key Findings -->
      <section class="section-block">
        <div class="section-label">KEY FINDINGS</div>
        <div class="findings-grid">
          <div
            v-for="(finding, i) in data.key_findings"
            :key="i"
            class="finding-card"
            :class="findingClass(i)"
          >
            <span class="finding-icon">{{ findingIcon(i) }}</span>
            <span class="finding-text">{{ finding }}</span>
          </div>
        </div>
      </section>

      <!-- Section G: Pipeline Overview -->
      <section class="section-block">
        <div class="section-label">7-STEP PIPELINE</div>
        <div class="card">
          <div class="pipeline">
            <div
              v-for="(step, i) in pipelineSteps"
              :key="i"
              class="pipe-step"
            >
              <div class="pipe-connector" v-if="i > 0">
                <div class="connector-line"></div>
                <div class="connector-arrow">&gt;</div>
              </div>
              <div class="pipe-box">
                <div class="pipe-num">{{ String(i + 1).padStart(2, '0') }}</div>
                <div class="pipe-name">{{ step.label }}</div>
                <div class="pipe-time">{{ step.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Section H: Links -->
      <section class="section-block">
        <div class="section-label">LINKS</div>
        <div class="links-row">
          <a
            href="https://apartresearch.com/project/parity-swarm-using-populationbased-social-simulation-to-discover-ai-safety-monitor-blind-spots-c9qc"
            target="_blank"
            rel="noopener noreferrer"
            class="link-card"
          >
            <span class="link-icon">[P]</span>
            <span class="link-label">Full Paper</span>
            <span class="link-sub">Apart Research</span>
          </a>
          <a
            href="https://github.com/m-zest/parity_swarn_v2.2"
            target="_blank"
            rel="noopener noreferrer"
            class="link-card"
          >
            <span class="link-icon">[G]</span>
            <span class="link-label">GitHub</span>
            <span class="link-sub">Source Code</span>
          </a>
          <a
            href="https://apartresearch.com"
            target="_blank"
            rel="noopener noreferrer"
            class="link-card"
          >
            <span class="link-icon">[H]</span>
            <span class="link-label">Hackathon</span>
            <span class="link-sub">AI Control Hackathon 2026</span>
          </a>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import * as d3 from 'd3'

const showBanner = ref(true)
const loaded = ref(false)
const data = ref(null)
const barChartRef = ref(null)

const pipelineSteps = [
  { label: 'Scenario', time: '~1 min' },
  { label: 'Ontology', time: '~1 min' },
  { label: 'Graph', time: '~1 min' },
  { label: 'Agents', time: '~2 min' },
  { label: 'Simulate', time: '~10 min' },
  { label: 'Report', time: '~10 min' },
  { label: 'Monitor', time: '~1 min' },
]

const shortName = (id) => {
  const map = {
    direct_attacker: 'Direct Atk',
    distraction_agent: 'Distraction',
    patient_planner: 'Patient Plan',
    incremental_thief: 'Incr. Thief',
    resource_abuser: 'Resource Ab.',
    social_engineer: 'Social Eng.',
    colluding_pair: 'Colluding',
    context_manipulator: 'Ctx Manip.',
    steganographic_agent: 'Stegano',
    alignment_faker: 'Align Faker',
  }
  return map[id] || id
}

const sortedScenarios = computed(() => {
  if (!data.value) return []
  return [...data.value.scenarios].sort((a, b) => (a.detection_rate_run1 ?? 999) - (b.detection_rate_run1 ?? 999))
})

const rateClass = (rate) => {
  if (rate === null || rate === undefined) return ''
  if (rate >= 90) return 'accent-green'
  if (rate >= 60) return 'accent-orange'
  return 'accent-red'
}

const scoreClass = (score) => {
  if (score === null || score === undefined) return ''
  if (score >= 7) return 'accent-red'
  if (score >= 5) return 'accent-orange'
  return 'accent-green'
}

const isHighlight = (s) => {
  return s.detection_rate_run1 !== null && s.detection_rate_run1 < 50
}

const findingClass = (i) => {
  if (i === 0) return 'finding-critical'
  if (i === 1) return 'finding-warning'
  return 'finding-positive'
}

const findingIcon = (i) => {
  if (i === 0) return '\u25CF'  // red dot
  if (i === 1) return '\u25CF'
  return '\u25CF'
}

const drawBarChart = () => {
  if (!barChartRef.value || !data.value) return

  const container = barChartRef.value
  container.innerHTML = ''

  const scenarios = [...data.value.scenarios].sort((a, b) => (a.detection_rate_run1 ?? 999) - (b.detection_rate_run1 ?? 999))

  const margin = { top: 20, right: 30, bottom: 80, left: 50 }
  const width = container.clientWidth - margin.left - margin.right
  const height = 320 - margin.top - margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x0 = d3.scaleBand()
    .domain(scenarios.map(s => shortName(s.id)))
    .range([0, width])
    .padding(0.3)

  const x1 = d3.scaleBand()
    .domain(['run1', 'run2'])
    .range([0, x0.bandwidth()])
    .padding(0.08)

  const y = d3.scaleLinear()
    .domain([0, 100])
    .range([height, 0])

  // Grid lines
  svg.selectAll('line.grid')
    .data([0, 25, 50, 75, 100])
    .enter()
    .append('line')
    .attr('class', 'grid')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', '#1a1a1a')
    .attr('stroke-width', 1)

  // Y axis labels
  svg.selectAll('text.y-label')
    .data([0, 25, 50, 75, 100])
    .enter()
    .append('text')
    .attr('x', -8)
    .attr('y', d => y(d) + 3)
    .attr('text-anchor', 'end')
    .attr('fill', '#888888')
    .attr('font-size', '9px')
    .attr('font-family', "'Courier New', Consolas, monospace")
    .text(d => d + '%')

  // Bars
  const groups = svg.selectAll('g.bar-group')
    .data(scenarios)
    .enter()
    .append('g')
    .attr('transform', d => `translate(${x0(shortName(d.id))},0)`)

  // Run 1 bars
  groups.append('rect')
    .attr('x', x1('run1'))
    .attr('y', d => y(d.detection_rate_run1 ?? 0))
    .attr('width', x1.bandwidth())
    .attr('height', d => height - y(d.detection_rate_run1 ?? 0))
    .attr('fill', '#f97316')
    .attr('opacity', 0.9)

  // Run 2 bars
  groups.append('rect')
    .attr('x', x1('run2'))
    .attr('y', d => y(d.detection_rate_run2 ?? 0))
    .attr('width', x1.bandwidth())
    .attr('height', d => height - y(d.detection_rate_run2 ?? 0))
    .attr('fill', '#3b82f6')
    .attr('opacity', 0.9)

  // X axis labels
  svg.selectAll('text.x-label')
    .data(scenarios)
    .enter()
    .append('text')
    .attr('x', d => x0(shortName(d.id)) + x0.bandwidth() / 2)
    .attr('y', height + 14)
    .attr('text-anchor', 'end')
    .attr('transform', d => `rotate(-40, ${x0(shortName(d.id)) + x0.bandwidth() / 2}, ${height + 14})`)
    .attr('fill', '#888888')
    .attr('font-size', '9px')
    .attr('font-family', "'Courier New', Consolas, monospace")
    .text(d => shortName(d.id))

  // Value labels on bars
  groups.append('text')
    .attr('x', x1('run1') + x1.bandwidth() / 2)
    .attr('y', d => y(d.detection_rate_run1 ?? 0) - 4)
    .attr('text-anchor', 'middle')
    .attr('fill', '#f97316')
    .attr('font-size', '8px')
    .attr('font-family', "'Courier New', Consolas, monospace")
    .text(d => d.detection_rate_run1 !== null ? d.detection_rate_run1 + '%' : '')

  groups.append('text')
    .attr('x', x1('run2') + x1.bandwidth() / 2)
    .attr('y', d => y(d.detection_rate_run2 ?? 0) - 4)
    .attr('text-anchor', 'middle')
    .attr('fill', '#3b82f6')
    .attr('font-size', '8px')
    .attr('font-family', "'Courier New', Consolas, monospace")
    .text(d => d.detection_rate_run2 !== null ? d.detection_rate_run2 + '%' : '')
}

onMounted(async () => {
  try {
    const res = await fetch('/data/results.json')
    data.value = await res.json()
    loaded.value = true
    await nextTick()
    drawBarChart()
    window.addEventListener('resize', drawBarChart)
  } catch (e) {
    console.error('Failed to load results:', e)
  }
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #080808;
}

.page-header {
  height: 44px;
  background: #0f0f0f;
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
  color: #888888;
  font-family: 'Courier New', Consolas, monospace;
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #22c55e;
  padding: 3px 10px;
  border: 1px solid rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.05);
  font-family: 'Courier New', Consolas, monospace;
}

.pulse {
  width: 5px;
  height: 5px;
  background: #22c55e;
  animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.loading-text {
  font-size: 11px;
  letter-spacing: 2px;
  color: #666;
  font-family: 'Courier New', Consolas, monospace;
  animation: blink 1.5s ease-in-out infinite;
}

.page-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Section labels */
.section-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 4px;
  color: #666;
  text-transform: uppercase;
  font-variant: small-caps;
  font-family: 'Courier New', Consolas, monospace;
}

/* Prototype banner */
.prototype-banner {
  background: #1a0f00;
  border: 1px solid #f97316;
  padding: 14px 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.banner-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.banner-icon {
  color: #f97316;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border: 1px solid #f97316;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  font-family: 'Courier New', Consolas, monospace;
}

.banner-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.banner-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #f97316;
  font-family: 'Courier New', Consolas, monospace;
}

.banner-desc {
  font-size: 11px;
  line-height: 1.6;
  color: #cccccc;
  font-family: 'Courier New', Consolas, monospace;
}

.banner-close {
  background: none;
  border: none;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  padding: 0 4px;
  flex-shrink: 0;
  font-family: 'Courier New', Consolas, monospace;
}

.banner-close:hover {
  color: #999;
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-cell {
  background: #0f0f0f;
  border: 1px solid #1a1a1a;
  padding: 16px;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #e0e0e0;
  line-height: 1;
  margin-bottom: 4px;
  font-family: 'Courier New', Consolas, monospace;
}

.stat-desc {
  font-size: 10px;
  color: #666;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
  font-family: 'Courier New', Consolas, monospace;
}

.stat-bar {
  height: 2px;
  background: #1a1a1a;
}

.stat-bar-fill {
  height: 100%;
  transition: width 0.6s ease;
}

.stat-bar-fill.green { background: #22c55e; }
.stat-bar-fill.blue { background: #3b82f6; }
.stat-bar-fill.orange { background: #f97316; }
.stat-bar-fill.red { background: #ef4444; }
.stat-bar-fill.neutral { background: #666; }

.accent-green { color: #22c55e !important; }
.accent-orange { color: #f97316 !important; }
.accent-red { color: #ef4444 !important; }

/* Category breakdown */
.cat-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #888;
  margin-bottom: 12px;
  font-family: 'Courier New', Consolas, monospace;
}

.cat-rates {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.cat-rate {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cat-rate-val {
  font-size: 22px;
  font-weight: 700;
  font-family: 'Courier New', Consolas, monospace;
}

.cat-rate-label {
  font-size: 9px;
  color: #666;
  font-family: 'Courier New', Consolas, monospace;
}

.orange-text { color: #f97316; }
.blue-text { color: #3b82f6; }

.cat-runs {
  font-size: 9px;
  color: #555;
  font-family: 'Courier New', Consolas, monospace;
}

/* Cards */
.card {
  background: #0f0f0f;
  border: 1px solid #1a1a1a;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #1a1a1a;
}

.card-title {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: #888;
  font-family: 'Courier New', Consolas, monospace;
}

.card-badge {
  font-size: 9px;
  font-weight: 500;
  color: #666;
  padding: 2px 8px;
  border: 1px solid #1a1a1a;
  letter-spacing: 0.5px;
  font-family: 'Courier New', Consolas, monospace;
}

/* Chart */
.chart-container {
  padding: 16px;
  min-height: 320px;
}

.chart-legend {
  padding: 10px 16px;
  display: flex;
  gap: 16px;
  border-top: 1px solid #1a1a1a;
}

.legend {
  font-size: 9px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 5px;
  font-family: 'Courier New', Consolas, monospace;
}

.dot {
  width: 6px;
  height: 6px;
}

.dot.green { background: #22c55e; }
.dot.orange { background: #f97316; }
.dot.blue { background: #3b82f6; }
.dot.red { background: #ef4444; }

/* Heatmap table */
.heatmap-table {
  font-family: 'Courier New', Consolas, monospace;
}

.heatmap-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1fr;
  gap: 1px;
  padding: 10px 16px;
  border-bottom: 1px solid #1a1a1a;
}

.heatmap-header .hm-col {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #666;
}

.heatmap-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1fr;
  gap: 1px;
  padding: 8px 16px;
  border-bottom: 1px solid #111;
  transition: background 0.15s;
}

.heatmap-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.heatmap-row.highlight-row {
  background: rgba(239, 68, 68, 0.05);
  border-left: 2px solid #ef4444;
}

.hm-col {
  font-size: 10px;
  color: #999;
}

.hm-col.hm-name {
  font-weight: 600;
  color: #ccc;
}

.hm-col.detected {
  color: #22c55e;
}

.hm-col.evaded {
  color: #ef4444;
}

/* Key Findings */
.findings-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.finding-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: #0f0f0f;
  border: 1px solid #1a1a1a;
}

.finding-card.finding-critical {
  border-left: 3px solid #ef4444;
}

.finding-card.finding-warning {
  border-left: 3px solid #f97316;
}

.finding-card.finding-positive {
  border-left: 3px solid #22c55e;
}

.finding-icon {
  flex-shrink: 0;
  font-size: 8px;
  line-height: 1;
  margin-top: 4px;
}

.finding-critical .finding-icon { color: #ef4444; }
.finding-warning .finding-icon { color: #f97316; }
.finding-positive .finding-icon { color: #22c55e; }

.finding-text {
  font-size: 11px;
  line-height: 1.6;
  color: #ccc;
  font-family: 'Courier New', Consolas, monospace;
}

/* Pipeline */
.pipeline {
  display: flex;
  align-items: center;
  padding: 20px 16px;
  overflow-x: auto;
}

.pipe-step {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.pipe-connector {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0 8px;
}

.connector-line {
  width: 20px;
  height: 1px;
  background: #1a1a1a;
}

.connector-arrow {
  color: #666;
  font-size: 10px;
  font-family: 'Courier New', Consolas, monospace;
}

.pipe-box {
  padding: 12px 16px;
  border: 1px solid #1a1a1a;
  background: #111;
  text-align: center;
  min-width: 100px;
}

.pipe-num {
  font-size: 16px;
  font-weight: 700;
  color: #ef4444;
  margin-bottom: 4px;
  font-family: 'Courier New', Consolas, monospace;
}

.pipe-name {
  font-size: 10px;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 2px;
  letter-spacing: 0.5px;
  font-family: 'Courier New', Consolas, monospace;
}

.pipe-time {
  font-size: 9px;
  color: #666;
  font-family: 'Courier New', Consolas, monospace;
}

/* Links */
.links-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.link-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
  background: #0f0f0f;
  border: 1px solid #1a1a1a;
  text-decoration: none;
  transition: border-color 0.15s;
}

.link-card:hover {
  border-color: #333;
}

.link-icon {
  font-size: 12px;
  color: #ef4444;
  font-family: 'Courier New', Consolas, monospace;
  margin-bottom: 4px;
}

.link-label {
  font-size: 12px;
  font-weight: 700;
  color: #e0e0e0;
  font-family: 'Courier New', Consolas, monospace;
}

.link-sub {
  font-size: 9px;
  color: #666;
  font-family: 'Courier New', Consolas, monospace;
}

/* Responsive */
@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .links-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
