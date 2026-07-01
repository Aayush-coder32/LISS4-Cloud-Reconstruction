import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#08131f",
        tide: "#0d3342",
        signal: "#ff9f1c",
        mint: "#68d391",
        cloud: "#f4efe6",
        panel: "#102435"
      },
      boxShadow: {
        panel: "0 18px 60px rgba(5, 14, 22, 0.28)"
      },
      borderRadius: {
        xl2: "1.4rem"
      }
    }
  },
  plugins: []
};

export default config;
