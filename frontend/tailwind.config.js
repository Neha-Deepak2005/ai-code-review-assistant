/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0e1116",       // page background
        panel: "#161b22",     // cards
        edge: "#262d38",      // borders
        mist: "#8b96a5",      // secondary text
        paper: "#e6ebf2",     // primary text
        accent: "#7c9ef8",    // periwinkle - buttons/links
        ok: "#3fb970",
        warn: "#d9a13b",
        bad: "#e5604c",
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}
