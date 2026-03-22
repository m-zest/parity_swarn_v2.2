<template>
  <router-view />
</template>

<script setup>
// Using Vue Router for page management
</script>

<style>
/* Global style reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  background-color: #0a0a0a;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #ffffff;
  background-color: #0a0a0a;
  min-height: 100vh;
}

/* Scrollbar styles */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #111111;
}

::-webkit-scrollbar-thumb {
  background: #333333;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555555;
}

/* Global button styles */
button {
  font-family: inherit;
}

/* Global dark theme variables */
:root {
  --bg-primary: #0a0a0a;
  --bg-card: #111111;
  --bg-elevated: #161616;
  --border-color: #222222;
  --border-hover: #333333;
  --text-primary: #ffffff;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --accent-dim: rgba(59, 130, 246, 0.1);
  --danger: #ef4444;
  --success: #22c55e;
  --warning: #f59e0b;
  --terminal-green: #4ade80;
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}
</style>
