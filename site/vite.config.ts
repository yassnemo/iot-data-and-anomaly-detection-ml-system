import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Default build (`npm run build`) outputs to ./dist — what Vercel serves when
// the project's Root Directory is `site`. A separate `npm run build:pages`
// re-targets ../docs for GitHub Pages. Relative `base` makes asset URLs work
// from a domain root (Vercel) or a /repo subpath (Pages) alike.
export default defineConfig({
  plugins: [react()],
  base: './',
})
