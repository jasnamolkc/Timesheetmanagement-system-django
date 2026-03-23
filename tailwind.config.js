/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./timesheet/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        'dark-navy': '#0f172a',
      }
    },
  },
  plugins: [],
}
