import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // The DOM renderer and 3D renderer must share the same React runtime.
    dedupe: ['react', 'react-dom', 'three'],
  },
  optimizeDeps: {
    // Prebundle the lazy-loaded viewer up front instead of rediscovering it
    // after the page has already loaded React from an older dependency graph.
    include: ['react', 'react-dom/client', '@react-three/fiber', '@react-three/drei'],
  },
  // Repository sites on GitHub Pages live under /<repository-name>/.
  base: '/damien-portfolio/',
})
