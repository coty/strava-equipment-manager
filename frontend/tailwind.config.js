/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        strava: {
          orange: '#FC4C02',
          'orange-dark': '#E34402',
        }
      }
    },
  },
  plugins: [],
}
