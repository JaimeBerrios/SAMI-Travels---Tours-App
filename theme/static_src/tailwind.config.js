/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Este archivo vive en theme/static_src/; las rutas son relativas a él.
    "../templates/**/*.html",
    "../../core/templates/**/*.html",
    "../../**/templates/**/*.html",
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
