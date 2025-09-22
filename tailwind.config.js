// tailwind.config.js

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Enable dark mode
  content: [
    './templates/**/*.html', // Scans all your templates
    './**/forms.py',       // Scans your forms for CSS classes
  ],
  theme: {
    extend: {
      colors: {
        
      }
    },
  },
  plugins: [],
}