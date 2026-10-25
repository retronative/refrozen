import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import docsPlugin from './plugins/docs.mjs'
import { base } from './scripts/site-config.mjs'

export default defineConfig({
  base,
  plugins: [vue(), tailwindcss(), docsPlugin()],
  server: { fs: { allow: ['..'] } },
  build: { target: 'es2022', cssCodeSplit: true },
})
