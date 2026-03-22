/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#1b998b', dark: '#158a7d' },
        surface: { DEFAULT: '#1a1a2e', light: '#252540' },
      },
    },
  },
  plugins: [],
}
