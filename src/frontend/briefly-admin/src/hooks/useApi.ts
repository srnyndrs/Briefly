import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { feedsApi, sourcesApi } from '@/api/client'
import { Feed, Source } from '@/types'

// Feeds hooks
export function useFeeds(page = 1, pageSize = 10) {
  return useQuery({
    queryKey: ['feeds', page, pageSize],
    queryFn: () => feedsApi.list(page, pageSize).then((res) => res.data),
  })
}

export function useFeed(id: string) {
  return useQuery({
    queryKey: ['feed', id],
    queryFn: () => feedsApi.get(id).then((res) => res.data),
    enabled: !!id,
  })
}

export function useCreateFeed() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Omit<Feed, 'id'>) => feedsApi.create(data).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] })
    },
  })
}

export function useUpdateFeed() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Feed> }) =>
      feedsApi.update(id, data).then((res) => res.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] })
      queryClient.invalidateQueries({ queryKey: ['feed', data.id] })
    },
  })
}

export function useDeleteFeed() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => feedsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] })
    },
  })
}

export function useToggleFeedStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: Feed['status'] }) =>
      feedsApi.toggleStatus(id, status).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] })
    },
  })
}

// Sources hooks
export function useSources(page = 1, pageSize = 10) {
  return useQuery({
    queryKey: ['sources', page, pageSize],
    queryFn: () => sourcesApi.list(page, pageSize).then((res) => res.data),
  })
}

export function useSource(id: string) {
  return useQuery({
    queryKey: ['source', id],
    queryFn: () => sourcesApi.get(id).then((res) => res.data),
    enabled: !!id,
  })
}

export function useCreateSource() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Omit<Source, 'id'>) =>
      sourcesApi.create(data).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })
}

export function useUpdateSource() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Source> }) =>
      sourcesApi.update(id, data).then((res) => res.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      queryClient.invalidateQueries({ queryKey: ['source', data.id] })
    },
  })
}

export function useDeleteSource() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => sourcesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })
}

export function useToggleSourceStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: Source['status'] }) =>
      sourcesApi.toggleStatus(id, status).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })
}
