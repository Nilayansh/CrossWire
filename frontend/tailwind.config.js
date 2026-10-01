/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Newsreader', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        canvas: '#FBFBFA',
        surface: '#FFFFFF',
        borderSubtle: '#EAEAEA',
        borderDark: '#111111',
        textMain: '#111111',
        textBody: '#1F2428',
        textMuted: '#57606A',
        bone: '#F7F6F3',
      },
      borderWidth: {
        '2.5': '2.5px',
      }
    },
  },
  plugins: [],
}
