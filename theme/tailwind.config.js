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
          navy: "#0B1F3A",
          "navy-dark": "#06152B",
          "navy-light": "#173F6B",
          red: "#E11D48",
          "red-dark": "#BE123C",
          "red-soft": "#FFF1F2",
          white: "#FFFFFF",
        },
      },
    },
  },
  plugins: [],
};
