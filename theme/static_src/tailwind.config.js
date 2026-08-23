/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../templates/**/*.html",
    "../../core/templates/**/*.html",
    "../../**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#0B1F3A",
          "navy-dark": "#06152B",
          "navy-light": "#173F6B",
          red: "#D71920",
          "red-dark": "#AA1016",
          "red-soft": "#FDEBEC",
          white: "#FFFFFF",
        },
      },
    },
  },
  plugins: [],
};
