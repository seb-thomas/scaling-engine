/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,astro}",
  ],
  darkMode: 'class',
  theme: {
    container: {
      center: true,
      padding: '1rem',
      screens: {
        DEFAULT: '1024px',
      },
    },
    extend: {
      fontFamily: {
        'serif': ['EB Garamond Variable', 'EB Garamond', 'serif'],
        'sans': ['Inter Variable', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

