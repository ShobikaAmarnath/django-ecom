/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Use class-based dark mode
  content: [
    './templates/**/*.html',
    './**/forms.py',
  ],
  theme: {
    extend: {
      colors: {
        // Semantic color tokens for "Cool Slate" theme
        primary: {
          DEFAULT: '#0ea5a4', // teal-slate
          600: '#0b8b86',
          700: '#0a6d69',
          800: '#075451'
        },
        accent: {
          DEFAULT: '#6366f1', // cool indigo accent
          600: '#4f46e5',
          700: '#4338ca'
        },
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          600: '#475569',
          800: '#1e293b',
          900: '#0f1724'
        },
        surface: {
          DEFAULT: '#ffffff',
          muted: '#f8fafc',
          dark: '#0b1220'
        },
        'text-main': '#0f1724',
        'text-muted': '#475569',
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b'
      },
      backgroundImage: theme => ({
        'btn-gradient': `linear-gradient(90deg, ${theme('colors.primary.DEFAULT')}, ${theme('colors.accent.DEFAULT')})`,
        'card-gradient': `linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.02))`
      }),
      boxShadow: {
        'soft-lg': '0 8px 30px rgba(16,24,40,0.08)',
        'elevated': '0 12px 40px rgba(2,6,23,0.14)'
      },
      borderRadius: {
        'xl': '1rem'
      },
      transitionProperty: {
        'colors': 'background-color, border-color, color, fill, stroke'
      },
      keyframes: {
        'spin-slow': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' }
        },
        'fade-in-up': {
          '0%': { opacity: 0, transform: 'translateY(6px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' }
        }
      },
      animation: {
        'spin-slow': 'spin-slow 1s linear infinite',
        'fade-in-up': 'fade-in-up .28s cubic-bezier(.2,.9,.3,1) both'
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
