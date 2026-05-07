import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        frost: {
          low: "#16a34a",
          elevated: "#facc15",
          high: "#f97316",
          extreme: "#dc2626",
        },
      },
    },
  },
} satisfies Config;
