/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./**/*.py",
    "./assets/**/*.{js,ts,jsx,tsx,css}",
    "./styles/**/*.css"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Noto Sans', 'sans-serif'],
        serif: ['Georgia', 'Cambria', 'Times New Roman', 'Times', 'serif'],
        mono: ['Fira Code', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace']
      },
      colors: {
        arete: {
          primary: '#1e40af',
          'primary-focus': '#1d4ed8',
          'primary-content': '#ffffff',
          secondary: '#7c3aed',
          'secondary-focus': '#8b5cf6', 
          'secondary-content': '#ffffff',
          accent: '#059669',
          'accent-focus': '#047857',
          'accent-content': '#ffffff',
          neutral: '#374151',
          'neutral-focus': '#1f2937',
          'neutral-content': '#f3f4f6',
          'base-100': '#ffffff',
          'base-200': '#f9fafb',
          'base-300': '#f3f4f6',
          'base-content': '#1f2937',
          info: '#0ea5e9',
          success: '#10b981',
          warning: '#f59e0b',
          error: '#ef4444'
        }
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem'
      },
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem'
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: '#374151',
            h1: {
              color: '#1f2937',
              fontWeight: '700'
            },
            h2: {
              color: '#1f2937', 
              fontWeight: '600'
            },
            h3: {
              color: '#1f2937',
              fontWeight: '600'
            },
            'blockquote p:first-of-type::before': false,
            'blockquote p:last-of-type::after': false,
            code: {
              backgroundColor: '#f3f4f6',
              padding: '0.125rem 0.25rem',
              borderRadius: '0.25rem',
              fontWeight: '400'
            },
            'code::before': false,
            'code::after': false
          }
        }
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('daisyui')
  ],
  daisyui: {
    themes: [
      {
        arete: {
          primary: '#1e40af',
          'primary-focus': '#1d4ed8',
          'primary-content': '#ffffff',
          secondary: '#7c3aed',
          'secondary-focus': '#8b5cf6',
          'secondary-content': '#ffffff',
          accent: '#059669',
          'accent-focus': '#047857',
          'accent-content': '#ffffff',
          neutral: '#374151',
          'neutral-focus': '#1f2937',
          'neutral-content': '#f3f4f6',
          'base-100': '#ffffff',
          'base-200': '#f9fafb',
          'base-300': '#f3f4f6',
          'base-content': '#1f2937',
          info: '#0ea5e9',
          success: '#10b981',
          warning: '#f59e0b',
          error: '#ef4444',
          '--rounded-box': '0.5rem',
          '--rounded-btn': '0.375rem',
          '--rounded-badge': '1.9rem',
          '--animation-btn': '0.25s',
          '--animation-input': '0.2s',
          '--btn-text-case': 'uppercase',
          '--btn-focus-scale': '0.95',
          '--border-btn': '1px',
          '--tab-border': '1px',
          '--tab-radius': '0.5rem'
        }
      },
      'light',
      'dark',
      'cupcake',
      'corporate',
      'synthwave',
      'retro',
      'cyberpunk',
      'valentine',
      'halloween',
      'garden',
      'forest',
      'aqua',
      'lofi',
      'pastel',
      'fantasy',
      'wireframe',
      'black',
      'luxury',
      'dracula',
      'cmyk',
      'autumn',
      'business',
      'acid',
      'lemonade',
      'night',
      'coffee',
      'winter'
    ],
    darkTheme: 'dark',
    base: true,
    styled: true,
    utils: true,
    rtl: false,
    prefix: '',
    logs: true
  }
};