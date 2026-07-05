/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        chat: {
          bg: "#212121",
          sidebar: "#171717",
          surface: "#2f2f2f",
          border: "#424242",
          muted: "#8e8e8e",
          accent: "#10a37f",
          user: "#303030",
        },
      },
      fontFamily: {
        sans: ["Söhne", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};