// Fonts are bundled from npm and served with the app, never fetched (D-21, NFR-2). IBM Plex Sans
// for everything, IBM Plex Mono for the console and file contents (D-101).
import '@fontsource-variable/ibm-plex-sans'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/600.css'
import './styles/tokens.css'
import './styles/base.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { createAppRouter } from './router'
import { useLabStore } from './stores/lab'
import { initTheme } from './theme'

initTheme()

const pinia = createPinia()
createApp(App).use(pinia).use(createAppRouter()).mount('#app')

void useLabStore(pinia).connect()
