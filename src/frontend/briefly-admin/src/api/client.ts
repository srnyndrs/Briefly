import axios, { AxiosInstance } from 'axios'
import { Feed, Source, ListResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Pre-generated development token to handle authorization locally
const DEV_AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJicmllZmx5LWFjY291bnQtc2VydmljZSIsImF1ZCI6ImJyaWVmbHktcHVibGljLWFwaSIsInR5cGUiOiJhY2Nlc3MiLCJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJzY29wZXMiOlsiYWRtaW4iXSwidHYiOjEsImV4cCI6MjAwMDAwMDAwMH0.focEO06JTr2vxCsd_tIhGGV-F3--m5tE4JKvvo4J4Qo'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available, fallback to development JWT
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token') || DEV_AUTH_TOKEN
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Mapper from backend FeedItemResponse to frontend Feed interface
const mapFeedItemToFeed = (item: any): Feed => ({
  id: item.article_id || '',
  title: item.title || '',
  description: item.description || '',
  url: item.canonical_url || '',
  sourceId: item.source_title || 'Unknown Source',
  status: 'active',
  lastUpdated: item.published_at || '',
  itemCount: 0,
})

// Mapper from backend SourceResponse to frontend Source interface
const mapSourceToFrontend = (item: any): Source => ({
  id: item.feed_id || '',
  name: item.title || 'Untitled Source',
  description: item.description || '',
  status: item.last_crawl_succeeded ? 'active' : 'inactive',
  feedCount: 1,
  createdAt: item.created_at || '',
})

// Feeds API
export const feedsApi = {
  list: async (page = 1, pageSize = 10) => {
    const limit = pageSize
    const offset = (page - 1) * pageSize
    const response = await apiClient.get<any>(`/feed?limit=${limit}&offset=${offset}`)
    
    const mappedItems = (response.data.items || []).map(mapFeedItemToFeed)
    const mappedData: ListResponse<Feed> = {
      items: mappedItems,
      total: response.data.total || 0,
      page,
      pageSize,
    }
    
    return {
      ...response,
      data: mappedData,
    }
  },

  get: async (id: string) => {
    const response = await apiClient.get<any>(`/feed/articles/${id}`)
    return {
      ...response,
      data: mapFeedItemToFeed(response.data),
    }
  },

  create: async (data: Omit<Feed, 'id'>) => {
    const payload = {
      url: data.url,
      title: data.title,
      description: data.description,
    }
    const response = await apiClient.post<any>('/sources', payload)
    return {
      ...response,
      data: mapFeedItemToFeed(response.data),
    }
  },

  update: async (id: string, data: Partial<Feed>) => {
    const payload = {
      title: data.title,
      description: data.description,
    }
    const response = await apiClient.patch<any>(`/sources/${id}`, payload)
    return {
      ...response,
      data: mapFeedItemToFeed(response.data),
    }
  },

  delete: (id: string) => apiClient.delete(`/sources/${id}`),

  toggleStatus: (id: string, status: Feed['status']) =>
    apiClient.patch(`/sources/${id}`, { status }),
}

// Sources API
export const sourcesApi = {
  list: async (page = 1, pageSize = 10) => {
    const response = await apiClient.get<any[]>('/sources')
    const mappedItems = (response.data || []).map(mapSourceToFrontend)
    
    const total = mappedItems.length
    const start = (page - 1) * pageSize
    const paginatedItems = mappedItems.slice(start, start + pageSize)
    
    const mappedData: ListResponse<Source> = {
      items: paginatedItems,
      total,
      page,
      pageSize,
    }
    
    return {
      ...response,
      data: mappedData,
    }
  },

  get: async (id: string) => {
    const response = await apiClient.get<any>(`/sources/${id}`)
    return {
      ...response,
      data: mapSourceToFrontend(response.data),
    }
  },

  create: async (data: Omit<Source, 'id'>) => {
    const payload = {
      url: (data as any).url || 'http://example.com/feed.xml',
      title: data.name,
      description: data.description,
    }
    const response = await apiClient.post<any>('/sources', payload)
    return {
      ...response,
      data: mapSourceToFrontend(response.data),
    }
  },

  update: async (id: string, data: Partial<Source>) => {
    const payload = {
      title: data.name,
      description: data.description,
    }
    const response = await apiClient.patch<any>(`/sources/${id}`, payload)
    return {
      ...response,
      data: mapSourceToFrontend(response.data),
    }
  },

  delete: (id: string) => apiClient.delete(`/sources/${id}`),

  toggleStatus: (id: string, status: Source['status']) =>
    apiClient.patch(`/sources/${id}`, { status }),
}

export default apiClient
