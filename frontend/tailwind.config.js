/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: 'var(--bg-main)',
          card: 'var(--bg-card)',
          panel: 'var(--bg-panel)',
          border: 'var(--border-color)',
          hover: 'var(--bg-hover)',
        },
        brand: {
          emerald: '#10b981',
          emeraldDark: '#059669',
          indigo: '#6366f1',
          indigoDark: '#4f46e5',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
