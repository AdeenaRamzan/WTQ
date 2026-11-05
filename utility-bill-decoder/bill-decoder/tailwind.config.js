export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {
    fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'], mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'] },
    colors: { bg: 'var(--bg)', card: 'var(--card)', line: 'var(--line)', ink: 'var(--ink)', mute: 'var(--mute)', acc: 'var(--acc)', accH: 'var(--accH)', tint: 'var(--tint)', soft: 'var(--soft)' },
    maxWidth: { page: '1280px' }
  } },
  plugins: []
}
