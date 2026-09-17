# frontend

- `npm run dev` (Vite, port 5173, proxies `/api` to `http://localhost:8000`)
- `npm run build` = `tsc -b && vite build`
- `npm run lint` = `oxlint` (config in `.oxlintrc.json`). No ESLint, no Prettier.

Layout: `src/main.tsx` mounts, `src/App.tsx` is the root component,
`src/index.css` holds the Tailwind v4 entry (loaded via `@tailwindcss/vite`).

Installed and intended: TanStack Query, React Router, React Hook Form, Zod.
Add nothing else without asking.
