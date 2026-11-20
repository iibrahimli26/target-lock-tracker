/** Design tokens. Colour means status and nothing else:
 *  green = locked, amber = unlocked, red = lost. Everything else is graphite. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: { 950: "#15181B", 900: "#1B1E22", 800: "#22262B", 700: "#2B3036", 600: "#3A4048", 500: "#5E666F", 400: "#8C949E", 200: "#DADDE1" },
        locked: "#46B978",
        unlocked: "#E3A53A",
        lost: "#E5534B",
        zone: "#9FB7D6",
      },
      fontFamily: {
        sans: ['"B612"', "Verdana", "Segoe UI", "sans-serif"],       // B612: designed for aircraft cockpit displays
        mono: ['"B612 Mono"', "Consolas", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
