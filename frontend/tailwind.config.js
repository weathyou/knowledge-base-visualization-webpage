export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        panel: '#0b1e46',
        line: '#2de2ff',
        glow: '#5ff6ff',
      },
      boxShadow: {
        neon: '0 0 20px rgba(52, 211, 255, 0.25)',
      },
      fontFamily: {
        display: ['"Microsoft YaHei UI"', '"Segoe UI"', 'sans-serif'],
      },
      backgroundImage: {
        stars:
          'radial-gradient(circle at 20% 20%, rgba(80,161,255,0.18), transparent 20%), radial-gradient(circle at 80% 30%, rgba(38,230,255,0.14), transparent 18%), radial-gradient(circle at 50% 80%, rgba(56,84,255,0.12), transparent 20%)',
      },
    },
  },
  plugins: [],
}
