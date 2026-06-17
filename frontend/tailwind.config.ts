import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-base": "var(--bg-base)",
        "bg-surface": "var(--bg-surface)",
        "bg-elevated": "var(--bg-elevated)",
        "border-subtle": "var(--border-subtle)",
        "border-active": "var(--border-active)",
        "accent-red": "var(--accent-red)",
        "accent-amber": "var(--accent-amber)",
        "accent-green": "var(--accent-green)",
        "accent-blue": "var(--accent-blue)",
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        "text-muted": "var(--text-muted)",
        "mono-accent": "var(--mono-accent)",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Space Grotesk", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
