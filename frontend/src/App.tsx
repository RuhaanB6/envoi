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

function App() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  })

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-6">
      <div className="w-full max-w-lg rounded-xl bg-white p-8 shadow">
        <h1 className="text-2xl font-bold text-slate-900">CS348 Project -- Stage 1</h1>
        <p className="mt-1 text-sm text-slate-500">
          React + Vite talking to FastAPI talking to Postgres.
        </p>

        <div className="mt-6 rounded-lg border border-slate-200 p-4">
          {isLoading && <p className="text-slate-500">Checking backend...</p>}

          {isError && (
            <p className="text-red-600">
              Could not reach /api/health: {(error as Error).message}
            </p>
          )}

          {data && (
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="font-medium text-slate-600">status</dt>
                <dd className="text-emerald-600 font-semibold">{data.status}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="font-medium text-slate-600">postgres</dt>
                <dd className="text-right text-slate-800">{data.postgres_version}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="font-medium text-slate-600">python</dt>
                <dd className="text-slate-800">{data.python_version}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="font-medium text-slate-600">fastapi</dt>
                <dd className="text-slate-800">{data.fastapi_version}</dd>
              </div>
            </dl>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
