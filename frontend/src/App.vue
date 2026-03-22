<template>
  <router-view />
</template>

<script setup>
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  background-color: #080808;
}

#app {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #e0e0e0;
  background-color: #080808;
  min-height: 100vh;
}

::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

::-webkit-scrollbar-track {
  background: #0a0a0a;
}

::-webkit-scrollbar-thumb {
  background: #2a2a2a;
}

::-webkit-scrollbar-thumb:hover {
  background: #3a3a3a;
}

button {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

input, textarea, select {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

:root {
  --bg-base: #080808;
  --bg-card: #0f0f0f;
  --bg-elevated: #141414;
  --bg-input: #0a0a0a;
  --border: #1a1a1a;
  --border-hover: #2a2a2a;
  --text-primary: #e0e0e0;
  --text-secondary: #888888;
  --text-muted: #555555;
  --red: #ef4444;
  --red-dim: rgba(239, 68, 68, 0.1);
  --red-border: rgba(239, 68, 68, 0.25);
  --orange: #f97316;
  --orange-dim: rgba(249, 115, 22, 0.1);
  --orange-border: rgba(249, 115, 22, 0.25);
  --green: #22c55e;
  --green-dim: rgba(34, 197, 94, 0.1);
  --green-border: rgba(34, 197, 94, 0.25);
  --terminal-green: #4ade80;
  --font-mono: 'JetBrains Mono', 'Courier New', monospace;

  /* Backward-compat aliases for existing components */
  --bg-primary: #080808;
  --border-color: #1a1a1a;
  --accent: #ef4444;
  --accent-hover: #dc2626;
  --accent-dim: rgba(239, 68, 68, 0.1);
  --danger: #ef4444;
  --success: #22c55e;
  --warning: #f97316;
  --font-sans: 'JetBrains Mono', 'Courier New', monospace;
}

a {
  color: inherit;
  text-decoration: none;
}
</style>
