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
        serif: ['EB Garamond', 'Georgia', 'Cambria', 'Times New Roman', 'Times', 'serif'],
        heading: ['Cinzel', 'serif'],
        greek: ['GFS Didot', 'serif'],
        mono: ['Fira Code', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace']
      },
      colors: {
        arete: {
          primary: '#2C3E50',
          'primary-focus': '#1a252f',
          'primary-content': '#FAF8F5',
          secondary: '#D4A574',
          'secondary-focus': '#C9A961',
          'secondary-content': '#3D3028',
          accent: '#C9A961',
          'accent-focus': '#B89751',
          'accent-content': '#3D3028',
          neutral: '#6B625A',
          'neutral-focus': '#3D3028',
          'neutral-content': '#FAF8F5',
          'base-100': '#FAF8F5',
          'base-200': '#F5F0E8',
          'base-300': '#E8DCC8',
          'base-content': '#3D3028',
          info: '#2C3E50',
          success: '#7B9E87',
          warning: '#C9A961',
          error: '#A85B52'
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
        classical: {
          primary: '#2C3E50',
          'primary-focus': '#1a252f',
          'primary-content': '#FAF8F5',
          secondary: '#D4A574',
          'secondary-focus': '#C9A961',
          'secondary-content': '#3D3028',
          accent: '#C9A961',
          'accent-focus': '#B89751',
          'accent-content': '#3D3028',
          neutral: '#6B625A',
          'neutral-focus': '#3D3028',
          'neutral-content': '#FAF8F5',
          'base-100': '#FAF8F5',
          'base-200': '#F5F0E8',
          'base-300': '#E8DCC8',
          'base-content': '#3D3028',
          info: '#2C3E50',
          success: '#7B9E87',
          warning: '#C9A961',
          error: '#A85B52',
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
      {
        arete: {
          primary: '#2C3E50',
          'primary-focus': '#1a252f',
          'primary-content': '#FAF8F5',
          secondary: '#D4A574',
          'secondary-focus': '#C9A961',
          'secondary-content': '#3D3028',
          accent: '#C9A961',
          'accent-focus': '#B89751',
          'accent-content': '#3D3028',
          neutral: '#6B625A',
          'neutral-focus': '#3D3028',
          'neutral-content': '#FAF8F5',
          'base-100': '#FAF8F5',
          'base-200': '#F5F0E8',
          'base-300': '#E8DCC8',
          'base-content': '#3D3028',
          info: '#2C3E50',
          success: '#7B9E87',
          warning: '#C9A961',
          error: '#A85B52',
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