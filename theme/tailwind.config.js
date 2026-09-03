/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "../core/templates/**/*.html",
    "../sami_admin/templates/**/*.html",
    "../core/**/*.py",
    "../sami_admin/**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#002756",
          "navy-dark": "#001A3D",
          "navy-light": "#174A80",
          red: "#FF131C",
          "red-dark": "#D90008",
          "red-soft": "#FFF0F1",
          white: "#FFFFFF",
        },
        // Alias legacy utility names to the corporate navy family so older
        // templates cannot introduce unrelated accent hues.
        blue: {
          50: "#eef4fb", 100: "#dce9f7", 200: "#b9d2ed", 300: "#86b2dc",
          700: "#174A80", 800: "#002756", 900: "#001A3D",
        },
        violet: {
          50: "#f0f4fa", 100: "#e1eaf5", 200: "#c4d5e9", 500: "#174A80",
          700: "#002756",
        },
      },
    },
  },
  plugins: [],
};
