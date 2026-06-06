import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Output goes to ../docs (committed). Relative `base` makes asset URLs work
// whether the site is served from a domain root (Vercel) or a /repo subpath
// (GitHub Pages) — no per-host config needed.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: '../docs',
    emptyOutDir: true,
  },
})
