import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { useTheme } from './composables/useTheme.js'

// Apply persisted theme/accent/density before first paint (no flash).
useTheme().apply()

createApp(App).mount('#app')
