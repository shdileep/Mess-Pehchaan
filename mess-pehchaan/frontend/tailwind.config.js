/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vit: {
          blue: '#003366',
          yellow: '#FFCC00',
          dark: '#002244'
        }
      }
    },
  },
  plugins: [],
}
