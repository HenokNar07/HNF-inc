// Uses an absolute config path rather than relying on tailwindcss's
// cwd-relative auto-discovery: whatever spawns this dev server may have a
// different process.cwd() than this directory (e.g. an editor task runner
// or preview tool launching from the repo root), which would otherwise
// cause Tailwind to silently fail to find tailwind.config.cjs and emit only
// its base/reset styles with no utility classes.
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default {
  plugins: {
    tailwindcss: { config: path.join(__dirname, 'tailwind.config.cjs') },
    autoprefixer: {},
  },
}
