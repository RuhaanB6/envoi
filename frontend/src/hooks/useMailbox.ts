import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import type { Filters, LetterDraft } from '../api'

export function useMailbox(userId: number, filters: Filters) {
  const client = useQueryClient()
  const refresh = async () => {
    await Promise.all([
      client.invalidateQueries({ queryKey: ['report', userId] }),
      client.invalidateQueries({ queryKey: ['options', userId] }),
    ])
  }
  const options = useQuery({ queryKey: ['options', userId], queryFn: () => api.options(userId) })
  const report = useQuery({ queryKey: ['report', userId, filters], queryFn: () => api.report(userId, filters) })
  const save = useMutation({ mutationFn: ({ draft, id }: { draft: LetterDraft; id?: number }) => api.save(userId, draft, id), onSuccess: refresh })
  const remove = useMutation({ mutationFn: (id: number) => api.remove(userId, id), onSuccess: refresh })
  return { options, report, save, remove }
}
