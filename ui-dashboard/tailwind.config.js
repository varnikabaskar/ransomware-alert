/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        cyber: {
          bg: "#090B10",
          panel: "#111622",
          panel2: "#0D1320",
          line: "#1F2937",
          neonBlue: "#39A0FF",
          neonGreen: "#36F9A2",
          neonRed: "#FF4D6D",
          neonAmber: "#FFC857",
          text: "#E5ECFF",
          muted: "#9FB2D9"
        },
      },
      boxShadow: {
        neonBlue: "0 0 0 1px rgba(57,160,255,0.25), 0 0 20px rgba(57,160,255,0.2)",
        neonRed: "0 0 0 1px rgba(255,77,109,0.3), 0 0 22px rgba(255,77,109,0.25)",
      },
      animation: {
        pulseSlow: "pulse 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
