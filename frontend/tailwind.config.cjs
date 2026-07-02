const path = require('node:path')

// Absolute paths, not cwd-relative ones -- whatever spawns this dev server
// may have a different process.cwd() than this directory (see the comment
// in postcss.config.js), which would otherwise make these globs match
// nothing and silently produce zero utility classes.
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    path.join(__dirname, "index.html"),
    path.join(__dirname, "src/**/*.{js,ts,jsx,tsx}"),
  ],
  theme: {
    extend: {
      colors: {
        surface: "var(--color-surface)",
        card: "var(--color-card)",
        border: "var(--color-border)",
        ink: "var(--color-ink)",
        "ink-muted": "var(--color-ink-muted)",
        primary: {
          DEFAULT: "var(--color-primary)",
          hover: "var(--color-primary-hover)",
          soft: "var(--color-primary-soft)",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
}
