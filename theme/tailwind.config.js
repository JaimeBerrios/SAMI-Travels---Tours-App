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
      },
    },
  },
  plugins: [],
};
