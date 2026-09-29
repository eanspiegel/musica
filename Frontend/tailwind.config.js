/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  theme: {
    extend: {
      // ─── Colors mapped from CSS custom properties ──────────────────────────
      colors: {
        brand: {
          DEFAULT: 'var(--color-brand)',
          hover: 'var(--color-brand-hover)',
          muted: 'var(--color-brand-muted)',
          subtle: 'var(--color-brand-subtle)',
        },
        surface: {
          0: 'var(--color-surface-0)',
          1: 'var(--color-surface-1)',
          2: 'var(--color-surface-2)',
          3: 'var(--color-surface-3)',
        },
        chrome: {
          DEFAULT: 'var(--color-chrome)',
          border: 'var(--color-chrome-border)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          'on-brand': 'var(--color-text-on-brand)',
          link: 'var(--color-text-link)',
        },
        feedback: {
          success: 'var(--color-success)',
          warning: 'var(--color-warning)',
          error: 'var(--color-error)',
          info: 'var(--color-info)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          focus: 'var(--color-border-focus)',
        },
      },

      // ─── Border radius ─────────────────────────────────────────────────────
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
        full: '9999px',
      },

      // ─── Font family ───────────────────────────────────────────────────────
      fontFamily: {
        sans: ['"Circular Std"', '"Circular"', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },

      // ─── Box shadows / elevation ───────────────────────────────────────────
      boxShadow: {
        'elevation-1': '0 2px 8px rgba(0,0,0,0.4)',
        'elevation-2': '0 4px 16px rgba(0,0,0,0.5)',
        'elevation-3': '0 8px 32px rgba(0,0,0,0.7)',
      },

      // ─── Transitions ───────────────────────────────────────────────────────
      transitionTimingFunction: {
        'out-smooth': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        'in-smooth': 'cubic-bezier(0.55, 0.06, 0.68, 0.19)',
        standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        micro: '80ms',
        fast: '150ms',
        standard: '250ms',
        deliberate: '350ms',
        page: '400ms',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      },
      animation: {
        'fade-in': 'fade-in 250ms cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards',
      }
    },
  },
  plugins: [],
}
