import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, emptyFilters } from './api'
import type { Filters, Letter, User } from './api'
import { useMailbox } from './hooks/useMailbox'
import { LetterForm } from './components/LetterForm'

const label = (value: string) => value === 'penpal' ? 'Pen pal' : value === 'in_transit' ? 'In transit' : value.charAt(0).toUpperCase() + value.slice(1)
const dateLabel = (value: string) => new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(new Date(value))

function Mailbox({ user }: { user: User }) {
  const [filters, setFilters] = useState<Filters>({ ...emptyFilters })
  const [compose, setCompose] = useState<Letter | 'new' | null>(null)
  const [reading, setReading] = useState<Letter | null>(null)
  const [deleting, setDeleting] = useState<Letter | null>(null)
  const [notice, setNotice] = useState('')
  const { report, options, save, remove } = useMailbox(user.id, filters)
  const changeFilter = (name: keyof Filters, value: string) => setFilters((old) => ({ ...old, [name]: value }))
  const data = report.data
  const activeFilters = Object.values(filters).some(Boolean)

  return <>
    <section className="flex flex-wrap items-end justify-between gap-6 pb-8 pt-10 sm:pt-14">
      <div><p className="text-xs font-semibold uppercase tracking-[.22em] text-teal-800">{user.display_name}’s correspondence</p>
        <h1 className="mt-3 font-serif text-4xl tracking-tight sm:text-5xl">Your mailbox, at a glance.</h1>
        <p className="mt-4 max-w-xl leading-7 text-stone-600">A place for the words you send, and the ones that find you.</p></div>
      <button className="primary" onClick={() => { save.reset(); setCompose('new') }} disabled={!options.data}>＋ Write a letter</button>
    </section>
    <div role="status" aria-live="polite" className="mb-4 min-h-5 text-sm text-teal-800">{notice}</div>
    <section aria-label="Mailbox report" className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
      {[['Matching letters', data?.matching_count], ['Average word count', data?.average_word_count], ['Sent', data?.sent_count], ['Received', data?.received_count]].map(([name, value]) =>
        <div key={name} className="rounded-xl border border-stone-200 bg-white/70 px-5 py-6"><p className="text-xs font-medium uppercase tracking-wider text-stone-500">{name}</p>
          <p className="mt-3 font-serif text-4xl tabular-nums" data-testid={String(name).toLowerCase().replaceAll(' ', '-')}>{report.isError ? '—' : value ?? '…'}</p></div>)}
    </section>
    <section className="rounded-2xl border border-stone-200 bg-white/75">
      <div className="border-b border-stone-200 p-5 sm:p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h2 className="font-serif text-2xl">Mailbox report</h2>
          <button className="text-sm text-teal-800 underline underline-offset-4 disabled:text-stone-400" disabled={!activeFilters} onClick={() => setFilters({ ...emptyFilters })}>Clear filters</button></div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <label className="filter-label">Correspondent<select className="field mt-2" value={filters.correspondent_id} onChange={(e) => changeFilter('correspondent_id', e.target.value)}>
            <option value="">All correspondents</option>{options.data?.correspondents.map((person) => <option key={person.id} value={person.id}>{person.display_name}</option>)}
          </select></label>
          <label className="filter-label">Mode<select className="field mt-2" value={filters.mode} onChange={(e) => changeFilter('mode', e.target.value)}>
            <option value="">All modes</option>{filters.mode && options.data && !options.data.modes.includes(filters.mode) && <option value={filters.mode}>{label(filters.mode)}</option>}{options.data?.modes.map((mode) => <option key={mode} value={mode}>{label(mode)}</option>)}
          </select></label>
          <label className="filter-label">Status<select className="field mt-2" value={filters.status} onChange={(e) => changeFilter('status', e.target.value)}>
            <option value="">All statuses</option>{filters.status && options.data && !options.data.statuses.includes(filters.status) && <option value={filters.status}>{label(filters.status)}</option>}{options.data?.statuses.map((status) => <option key={status} value={status}>{label(status)}</option>)}
          </select></label>
          <label className="filter-label">From (UTC)<input className="field mt-2" type="date" value={filters.date_from} onChange={(e) => changeFilter('date_from', e.target.value)} onBlur={(e) => changeFilter('date_from', e.target.value)} /></label>
          <label className="filter-label">Through (UTC)<input className="field mt-2" type="date" value={filters.date_to} onChange={(e) => changeFilter('date_to', e.target.value)} onBlur={(e) => changeFilter('date_to', e.target.value)} /></label>
        </div>
        <p className="mt-4 text-xs leading-5 text-stone-500">Both sent and received letters. Dates filter when a letter was created; both boundary dates are included. Word counts are calculated in PostgreSQL.</p>
      </div>
      {(report.isError || options.isError) && <div role="alert" className="m-5 rounded-lg bg-rose-50 p-4 text-sm text-rose-800">{report.error?.message || options.error?.message}<button className="ml-3 underline" onClick={() => { void report.refetch(); void options.refetch() }}>Retry</button></div>}
      {report.isPending && <p className="p-8 text-stone-500">Opening your mailbox…</p>}
      {data && !report.isError && <>
        <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-stone-50 text-xs uppercase tracking-wide text-stone-500"><tr><th className="p-5 font-medium">Letter</th><th className="p-5 font-medium">Correspondent</th><th className="p-5 font-medium">Mode / status</th><th className="p-5 font-medium">Created</th><th className="p-5 text-right font-medium">Words</th><th className="p-5 text-right font-medium">Actions</th></tr></thead>
          <tbody>{data.letters.map((letter) => <tr key={letter.id} className="border-t border-stone-100 hover:bg-stone-50/70">
            <td className="max-w-[280px] p-5"><button className="text-left font-semibold text-stone-800 underline-offset-4 hover:underline" onClick={() => setReading(letter)}>{letter.subject}</button><p className="mt-1 text-xs text-stone-500">{letter.is_sent ? 'Sent' : 'Received'} · #{letter.id}</p></td>
            <td className="p-5">{letter.is_sent ? letter.recipient_name : letter.sender_name}</td>
            <td className="p-5"><p>{label(letter.mode)}</p><span className={`mt-1 inline-block rounded-full px-2 py-1 text-[11px] ${letter.status === 'draft' ? 'bg-amber-50 text-amber-900' : 'bg-teal-50 text-teal-900'}`}>{label(letter.status)}</span></td>
            <td className="whitespace-nowrap p-5 text-stone-500">{dateLabel(letter.created_at)}</td><td className="p-5 text-right tabular-nums">{letter.word_count}</td>
            <td className="p-5 text-right">{letter.can_edit ? <div className="flex justify-end gap-3"><button className="text-teal-800 underline underline-offset-4" aria-label={`Edit ${letter.subject}`} onClick={() => { save.reset(); setCompose(letter) }}>Edit</button><button className="text-rose-700 underline underline-offset-4" aria-label={`Delete ${letter.subject}`} onClick={() => { remove.reset(); setDeleting(letter) }}>Delete</button></div> : <span className="text-xs text-stone-400">Read only</span>}</td>
          </tr>)}</tbody>
        </table></div>
        {!data.letters.length && <div className="p-12 text-center"><p className="font-serif text-2xl">No letters here yet.</p><p className="mt-3 text-sm text-stone-500">{activeFilters ? 'Try a different filter or clear your selection.' : 'Start with a few words to someone you know.'}</p></div>}
        <div className="flex flex-wrap justify-between gap-2 border-t border-stone-200 px-5 py-4 text-xs text-stone-500"><span>{data.matching_count} matching {data.matching_count === 1 ? 'letter' : 'letters'}{report.isFetching ? ' · Updating…' : ''}</span><span>Only your own drafts can be edited or deleted.</span></div>
      </>}
    </section>
    {compose && options.data && <LetterForm key={compose === 'new' ? 'new' : compose.id} letter={compose === 'new' ? undefined : compose} options={options.data} pending={save.isPending} error={save.error?.message} onClose={() => setCompose(null)} onSave={(draft) => save.mutate({ draft, id: compose === 'new' ? undefined : compose.id }, { onSuccess: () => { setNotice(compose === 'new' ? 'Draft saved. Your report is up to date.' : 'Draft updated. Your report is up to date.'); setCompose(null) } })} />}
    {deleting && <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/45 p-4"><section role="dialog" aria-modal="true" aria-labelledby="delete-heading" className="w-full max-w-md rounded-2xl bg-[#fffdf8] p-7 shadow-xl"><h2 id="delete-heading" className="font-serif text-2xl">Delete this draft?</h2><p className="mt-4 text-sm leading-6 text-stone-600">“{deleting.subject}” will be permanently removed.</p>{remove.error && <p role="alert" className="mt-3 text-sm text-rose-800">{remove.error.message}</p>}<div className="mt-6 flex justify-end gap-3"><button className="secondary" disabled={remove.isPending} onClick={() => setDeleting(null)}>Keep draft</button><button className="primary bg-rose-800 hover:bg-rose-900" disabled={remove.isPending} onClick={() => remove.mutate(deleting.id, { onSuccess: () => { setDeleting(null); setNotice('Draft deleted. Your report is up to date.') } })}>{remove.isPending ? 'Deleting…' : 'Delete draft'}</button></div></section></div>}
    {reading && <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/45 p-4"><section role="dialog" aria-modal="true" aria-labelledby="read-heading" className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-[#fffdf8] p-8 shadow-xl"><div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-widest text-teal-800">{reading.sender_name} → {reading.recipient_name}</p><h2 id="read-heading" className="mt-3 font-serif text-3xl">{reading.subject}</h2><p className="mt-3 text-xs text-stone-500">{dateLabel(reading.created_at)} · {label(reading.status)} · {reading.word_count} words</p></div><button aria-label="Close letter" onClick={() => setReading(null)} className="px-2 text-2xl">×</button></div><p className="mt-8 whitespace-pre-wrap break-words font-serif text-lg leading-8 text-stone-700">{reading.body}</p></section></div>}
  </>
}

export default function App() {
  const users = useQuery({ queryKey: ['users'], queryFn: api.users })
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selectedUser = users.data?.find((user) => user.id === selectedId) ?? users.data?.find((user) => user.username === 'ruhaan') ?? users.data?.[0]
  return <div className="min-h-screen bg-[#f6f5f0] text-stone-800">
    <header className="border-b border-stone-200 bg-[#fffdf8]"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-5 sm:px-8"><div className="flex items-center gap-4"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-900 font-serif text-2xl text-white" aria-hidden="true">e</span><div><p className="font-serif text-3xl tracking-tight">envoi<span className="text-teal-700">.</span></p><p className="text-[10px] uppercase tracking-[.18em] text-stone-500">Letters, done right</p></div></div>
      <label className="flex items-center gap-3 text-xs font-medium text-stone-500">Demo identity<select aria-label="Demo identity" className="field min-w-40" value={selectedUser?.id ?? ''} onChange={(event) => setSelectedId(Number(event.target.value))} disabled={!users.data?.length}>{users.data?.map((user) => <option key={user.id} value={user.id}>{user.display_name}</option>)}</select></label></div></header>
    <main className="mx-auto max-w-7xl px-5 pb-12 sm:px-8">{users.isPending && <p className="py-16 text-stone-600">Connecting to your mailbox…</p>}{users.error && <div role="alert" className="my-10 rounded-xl bg-rose-50 p-6 text-rose-800">Could not load demo users. {users.error.message}<button className="ml-3 underline" onClick={() => void users.refetch()}>Retry</button></div>}{users.data?.length === 0 && <p className="py-16">No demo users are available. Load the demo data to begin.</p>}{selectedUser && <Mailbox key={selectedUser.id} user={selectedUser} />}
      <footer className="mt-8 flex flex-wrap justify-between gap-3 text-xs leading-6 text-stone-500"><span>Envoi · CS348 Stage 2</span><span>Local demo · Identity selection is not authentication · PostgreSQL-backed</span></footer>
    </main>
  </div>
}
