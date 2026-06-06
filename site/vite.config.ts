import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Built site is published via GitHub Pages from the repo's /docs folder.
// `base` must match the repository name so asset URLs resolve on Pages.
export default defineConfig({
  plugins: [react()],
  base: '/iot-data-and-anomaly-detection-ml-system/',
  build: {
    outDir: '../docs',
    emptyOutDir: true,
  },
})
