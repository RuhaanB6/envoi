export interface User { id: number; username: string; display_name: string }
export interface Penpalship { id: number; correspondent_id: number; correspondent_name: string; status: string }
export interface Options { recipients: User[]; penpalships: Penpalship[]; correspondents: User[]; modes: string[]; statuses: string[] }
export type Mode = 'direct' | 'penpal'
export interface LetterDraft { recipient_id: number; penpalship_id: number | null; subject: string; body: string; mode: Mode }
export interface Letter extends LetterDraft {
  id: number; sender_id: number; status: string; created_at: string; updated_at: string;
  sender_name: string; recipient_name: string; word_count: number; is_sent: boolean; can_edit: boolean;
}
export interface Report { matching_count: number; average_word_count: number; sent_count: number; received_count: number; letters: Letter[] }
export interface Filters { correspondent_id: string; mode: string; status: string; date_from: string; date_to: string }
export const emptyFilters: Filters = { correspondent_id: '', mode: '', status: '', date_from: '', date_to: '' }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init, credentials: 'include', headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const error = await response.json().catch(() => null)
    const detail = error?.detail
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail)
      ? detail.map((item: { msg: string }) => item.msg).join(' ') : `Request failed (${response.status}).`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export const api = {
  users: () => request<User[]>('/users'),
  options: (userId: number) => request<Options>(`/options?user_id=${userId}`),
  report: (userId: number, filters: Filters) => {
    const query = new URLSearchParams({ user_id: String(userId) })
    Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value) })
    return request<Report>(`/report?${query}`)
  },
  save: (userId: number, draft: LetterDraft, id?: number) => request<{ id: number }>(
    `/letters${id ? `/${id}` : ''}?user_id=${userId}`,
    { method: id ? 'PUT' : 'POST', body: JSON.stringify(draft) },
  ),
  remove: (userId: number, id: number) => request<void>(`/letters/${id}?user_id=${userId}`, { method: 'DELETE' }),
}
