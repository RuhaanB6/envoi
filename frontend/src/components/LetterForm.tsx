import { useForm, useWatch } from 'react-hook-form'
import type { FieldErrors, Resolver } from 'react-hook-form'
import { z } from 'zod'
import type { Letter, LetterDraft, Options } from '../api'

const schema = z.object({
  recipient_id: z.number().int().positive('Choose a recipient.'),
  penpalship_id: z.number().int().positive().nullable(),
  subject: z.string().trim().min(1, 'Add a subject.').max(200),
  body: z.string().trim().min(1, 'Write a letter.').max(50000),
  mode: z.enum(['direct', 'penpal']),
}).superRefine((value, context) => {
  if (value.mode === 'penpal' && !value.penpalship_id)
    context.addIssue({ code: 'custom', path: ['penpalship_id'], message: 'Choose a pen-palship.' })
})

const resolver: Resolver<LetterDraft> = async (values) => {
  const result = schema.safeParse(values)
  if (result.success) return { values: result.data, errors: {} }
  const errors: FieldErrors<LetterDraft> = {}
  for (const issue of result.error.issues) {
    const key = issue.path[0] as keyof LetterDraft
    errors[key] = { type: 'validate', message: issue.message }
  }
  return { values: {}, errors }
}

interface Props {
  letter?: Letter; options: Options; pending: boolean; error?: string;
  onSave: (draft: LetterDraft) => void; onClose: () => void;
}

export function LetterForm({ letter, options, pending, error, onSave, onClose }: Props) {
  const { register, handleSubmit, control, setValue, formState: { errors } } = useForm<LetterDraft>({
    resolver, defaultValues: letter ? { recipient_id: letter.recipient_id, penpalship_id: letter.penpalship_id,
      subject: letter.subject, body: letter.body, mode: letter.mode }
      : { recipient_id: 0, penpalship_id: null, subject: '', body: '', mode: 'direct' },
  })
  const mode = useWatch({ control, name: 'mode' })
  const recipient = useWatch({ control, name: 'recipient_id' })
  const pairs = options.penpalships.filter((pair) => pair.correspondent_id === recipient)
  const messages = Object.values(errors).map((item) => item.message).filter(Boolean)

  return <div className="fixed inset-0 z-30 flex items-center justify-center overflow-y-auto bg-slate-950/45 p-4">
    <section role="dialog" aria-modal="true" aria-labelledby="compose-heading" className="my-auto max-h-[94vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-[#fffdf8] p-6 shadow-2xl sm:p-8">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div><p className="text-xs font-semibold uppercase tracking-[.2em] text-teal-800">A little correspondence</p>
          <h2 id="compose-heading" className="mt-2 font-serif text-3xl">{letter ? 'Edit your draft' : 'Write a letter'}</h2></div>
        <button type="button" onClick={onClose} disabled={pending} aria-label="Close letter form" className="rounded-lg px-3 py-1 text-2xl hover:bg-stone-100">×</button>
      </div>
      <form onSubmit={handleSubmit(onSave)} className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium">To
            <select {...register('recipient_id', { valueAsNumber: true, onChange: () => setValue('penpalship_id', null) })} className="field mt-2" autoFocus>
              <option value={0}>Choose a recipient</option>
              {options.recipients.map((person) => <option key={person.id} value={person.id}>{person.display_name} (@{person.username})</option>)}
            </select></label>
          <label className="text-sm font-medium">Letter mode
            <select {...register('mode', { onChange: () => setValue('penpalship_id', null) })} className="field mt-2">
              <option value="direct">Direct</option><option value="penpal">Pen pal</option>
            </select></label>
        </div>
        {mode === 'penpal' && <label className="block text-sm font-medium">Pen-palship
          <select {...register('penpalship_id', { setValueAs: (value: string) => value ? Number(value) : null })} className="field mt-2">
            <option value="">Choose an existing pen-palship</option>
            {pairs.map((pair) => <option key={pair.id} value={pair.id}>With {pair.correspondent_name} · #{pair.id}</option>)}
          </select>
          {!pairs.length && <span className="mt-2 block text-xs font-normal text-stone-600">No active pen-palship with this recipient. Choose another recipient or use direct mode.</span>}
        </label>}
        <label className="block text-sm font-medium">Subject<input {...register('subject')} maxLength={200} className="field mt-2" placeholder="What’s on your mind?" /></label>
        <label className="block text-sm font-medium">Your letter<textarea {...register('body')} maxLength={50000} rows={9} className="field mt-2 resize-y font-serif text-base leading-7" placeholder="Dear friend…" /></label>
        {(messages.length > 0 || error) && <div role="alert" className="rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error || messages.join(' ')}</div>}
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-stone-200 pt-5">
          <p className="max-w-xs text-xs leading-5 text-stone-500">Saved as a draft. This demo does not send or deliver letters.</p>
          <div className="flex gap-3"><button type="button" className="secondary" onClick={onClose} disabled={pending}>Cancel</button>
            <button type="submit" className="primary" disabled={pending}>{pending ? 'Saving…' : letter ? 'Save changes' : 'Save draft'}</button></div>
        </div>
      </form>
    </section>
  </div>
}
