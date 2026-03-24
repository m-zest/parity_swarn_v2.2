<template>
  <div class="shell">
    <!-- Dot grid background -->
    <div class="dot-grid"></div>

    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-diamond">&loz;</span>
        <span class="brand-text">PARITY SWARM</span>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ active: $route.path === item.to }"
        >
          <span class="nav-indicator"></span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.gpu" class="gpu-badge">GPU</span>
          <span class="nav-key">{{ item.key }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <a
          href="https://github.com/m-zest/parity_swarn_v2.2/"
          target="_blank"
          rel="noopener noreferrer"
          class="github-link"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          <span>GitHub</span>
        </a>
        <span class="version-tag">v2.2</span>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
const navItems = [
  { to: '/', label: 'DASHBOARD', key: '01', gpu: false },
  { to: '/launch', label: 'LAUNCH SWARM', key: '02', gpu: true },
  { to: '/results', label: 'RESULTS', key: '03', gpu: true },
  { to: '/terminal', label: 'TERMINAL', key: '04', gpu: true },
  { to: '/history', label: 'HISTORY', key: '05', gpu: true },
]
</script>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
  position: relative;
}

.dot-grid {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: radial-gradient(circle, #1a1a1a 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
  z-index: 0;
}

.sidebar {
  width: 200px;
  min-height: 100vh;
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
}

.sidebar-brand {
  padding: 20px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-diamond {
  color: var(--red);
  font-size: 14px;
  line-height: 1;
}

.brand-text {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--text-primary);
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 10px 16px;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 1.5px;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s, background 0.15s;
  text-decoration: none;
  position: relative;
}

.nav-link:hover {
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.02);
}

.nav-link.active {
  color: var(--red);
}

.nav-indicator {
  width: 2px;
  height: 16px;
  margin-right: 12px;
  background: transparent;
  transition: background 0.15s;
}

.nav-link.active .nav-indicator {
  background: var(--red);
}

.nav-label {
  flex: 1;
}

.gpu-badge {
  font-size: 7px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--orange);
  border: 1px solid var(--orange-border);
  padding: 1px 4px;
  margin-left: auto;
  margin-right: 6px;
  opacity: 0.7;
}

.nav-key {
  font-size: 9px;
  color: var(--text-muted);
  opacity: 0.5;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.github-link {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.15s;
}

.github-link:hover {
  color: var(--text-secondary);
}

.version-tag {
  font-size: 9px;
  color: var(--text-muted);
  padding: 2px 6px;
  border: 1px solid var(--border);
  letter-spacing: 0.5px;
}

.main-content {
  flex: 1;
  margin-left: 200px;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .main-content {
    margin-left: 0;
  }
}
</style>
