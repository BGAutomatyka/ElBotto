import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// GH Pages requires a base path 
const baseFromEnv = process.env.VITE_BASE || '/'

export default defineConfig({
  base: baseFromEnv,
  plugins: [react()],
})
