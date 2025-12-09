/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        surface: '#111111',
        'surface-highlight': '#1a1a1a',
        primary: '#00ff9d', // Cyber green
        'primary-dim': 'rgba(0, 255, 157, 0.1)',
        secondary: '#00d2ff', // Cyber blue
        accent: '#ff0055', // Cyber red
        text: '#e0e0e0',
        'text-dim': '#808080',
        border: '#333333',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 255, 157, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 255, 157, 0.6)' },
        }
      }
    },
  },
  plugins: [],
}
