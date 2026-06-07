import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // IEEE-style dark blue + petrol/teal accents on a very light gray canvas.
        ieee: {
          DEFAULT: "#00629B",
          dark: "#003B5C",
          light: "#E6F0F6",
        },
        petrol: "#0E7C7B",
        canvas: "#F4F6F8",
      },
    },
  },
  plugins: [],
};

export default config;
