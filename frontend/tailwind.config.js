/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: "#0e1513",
        "surface-container": "#1a211f",
        "surface-container-low": "#161d1b",
        "surface-container-high": "#252b2a",
        "surface-container-highest": "#2f3634",
        "surface-variant": "#2f3634",
        "on-surface": "#dde4e1",
        "on-surface-variant": "#bbcac6",
        "outline-variant": "#3c4947",
        primary: "#4fdbc8",
        "primary-container": "#14b8a6",
        "on-primary": "#003731",
        secondary: "#ffb95f",
        "secondary-container": "#ee9800",
        "tertiary-container": "#f38764",
        error: "#ffb4ab",
        "error-container": "#93000a",
        "on-error-container": "#ffdad6",
      },
      maxWidth: {
        "container-max": "800px",
      },
      spacing: {
        md: "16px",
        sm: "8px",
        xs: "4px",
        lg: "24px",
        xl: "40px",
      },
      fontFamily: {
        sans: ["Geist", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        lg: "0.25rem",
        xl: "0.5rem",
      },
    },
  },
  plugins: [],
};
