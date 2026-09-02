import { useQuery } from '@tanstack/react-query'

// Mirrors the JSON shape returned by GET /api/health in the backend.
interface HealthResponse {
  status: string
  postgres_version: string
  python_version: string
  fastapi_version: string
}

async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch('/api/health')
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status}`)
  }
  return res.json()
}

// The backend returns Postgres' full banner ("PostgreSQL 17.6 (Debian ...) on
// aarch64 ..."), which is too long for a table row. Pull out the leading
// "PostgreSQL <version>" for display and keep the rest for the footer.
function shortPostgresVersion(full: string): string {
  return full.match(/^PostgreSQL [\d.]+/)?.[0] ?? full
}

function StatusPill({ state }: { state: 'loading' | 'ok' | 'error' }) {
  const styles = {
    loading: 'bg-amber-400/10 text-amber-300 ring-amber-400/30',
    ok: 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/30',
    error: 'bg-rose-400/10 text-rose-300 ring-rose-400/30',
  }[state]

  const label = { loading: 'connecting', ok: 'connected', error: 'unreachable' }[state]

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs
                  font-medium ring-1 ring-inset ${styles}`}
    >
      <span className="relative flex h-2 w-2">
        {state === 'ok' && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
        )}
        <span className="relative inline-flex h-2 w-2 rounded-full bg-current" />
      </span>
      {label}
    </span>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-white/5 py-3 last:border-0">
      <dt className="text-sm text-slate-400">{label}</dt>
      <dd className="font-mono text-sm text-slate-100">{value}</dd>
    </div>
  )
}

function App() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  })

  const state = isLoading ? 'loading' : isError ? 'error' : 'ok'

  return (
    <div className="min-h-screen bg-slate-950 bg-[radial-gradient(ellipse_at_top,#1e293b,#020617)] px-6 py-16">
      <main className="mx-auto w-full max-w-xl">
        <header className="text-center">
          <h1 className="bg-gradient-to-r from-sky-300 via-indigo-300 to-fuchsia-300 bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-6xl">
            Hello, World!
          </h1>
          <p className="mt-4 text-slate-400">
            CS348 Project &mdash; Stage 1. React and Vite talking to FastAPI,
            talking to Postgres.
          </p>
        </header>

        <section className="mt-10 rounded-2xl border border-white/10 bg-white/5 p-6 shadow-2xl backdrop-blur">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200">Stack health</h2>
            <StatusPill state={state} />
          </div>

          <div className="mt-4">
            {isLoading && (
              <p className="py-6 text-center text-sm text-slate-400">
                Checking the backend&hellip;
              </p>
            )}

            {isError && (
              <div className="rounded-lg bg-rose-500/10 p-4 text-sm text-rose-300">
                <p className="font-medium">Could not reach /api/health</p>
                <p className="mt-1 text-rose-300/70">{(error as Error).message}</p>
                <p className="mt-3 text-rose-300/70">
                  Is the backend running on port 8000?
                </p>
              </div>
            )}

            {data && (
              <>
                <dl>
                  <Row label="Postgres" value={shortPostgresVersion(data.postgres_version)} />
                  <Row label="Python" value={data.python_version} />
                  <Row label="FastAPI" value={data.fastapi_version} />
                </dl>
                <p className="mt-4 border-t border-white/5 pt-4 font-mono text-[11px] leading-relaxed text-slate-500">
                  {data.postgres_version}
                </p>
              </>
            )}
          </div>
        </section>

        <p className="mt-6 text-center text-xs text-slate-500">
          Every value above came from a live <code className="font-mono text-slate-400">SELECT version()</code> query.
        </p>
      </main>
    </div>
  )
}

export default App
