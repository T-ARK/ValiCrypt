/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        heading: ['"Syne"', '"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        vault: {
          bg: '#05020c',
          deep: '#030107',
          surface: '#0d061c',
          card: '#120826',
          border: 'rgba(168, 85, 247, 0.18)',
        },
      },
      boxShadow: {
        'glow-sm': '0 0 15px rgba(168, 85, 247, 0.3)',
        'glow-md': '0 0 30px rgba(168, 85, 247, 0.45)',
        'glow-lg': '0 0 50px rgba(168, 85, 247, 0.6)',
        'glow-laser': '0 0 15px #d946ef, 0 0 35px #a855f7',
        'glow-card': '0 0 40px -10px rgba(168, 85, 247, 0.45), inset 0 1px 0 0 rgba(216, 180, 254, 0.3)',
      },
      backgroundImage: {
        'purple-radial': 'radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.35) 0%, rgba(126, 34, 206, 0.18) 35%, rgba(5, 2, 12, 0) 70%)',
        'purple-bottom-radial': 'radial-gradient(circle at 50% 100%, rgba(192, 132, 252, 0.25) 0%, rgba(126, 34, 206, 0.1) 40%, rgba(5, 2, 12, 0) 70%)',
        'laser-gradient': 'linear-gradient(90deg, transparent 0%, #a855f7 25%, #f472b6 50%, #a855f7 75%, transparent 100%)',
        'laser-gradient-bright': 'linear-gradient(90deg, transparent 0%, #c084fc 20%, #ffffff 50%, #e879f9 80%, transparent 100%)',
      },
    },
  },
  plugins: [],
}
