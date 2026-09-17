---
paths: ["frontend/src/**"]
---

# Frontend conventions

- All server state goes through TanStack Query. No `useEffect` + `fetch`, no
  server data in `useState`, no global store.
- Every network call goes through the single api client module (`src/api/`),
  which owns the base URL, `credentials: "include"`, and error unwrapping.
  Components and hooks never call `fetch` directly.
- Query keys are arrays that mirror the route: `["letters", { status }]`.
  Mutations invalidate the keys they affect; do not hand-patch the cache.
- Forms: React Hook Form with a Zod resolver. The Zod schema is the single
  source of validation truth on the client; it mirrors the API contract but is
  never the enforcement point — the server decides.
- Styling is Tailwind utility classes only. No CSS modules, no styled-components,
  no inline `style` except for genuinely dynamic values (transit animations).
- Components stay dumb: they render props and call callbacks. Data fetching sits
  in hooks, business rules sit in the backend. If a component is deciding whether
  a letter may be edited, that decision belongs in the API response.
- Type imports use `import type`. Nothing is `any`.
