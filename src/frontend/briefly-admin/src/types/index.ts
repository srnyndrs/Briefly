export interface Feed {
  id: string
  title: string
  description?: string
  url: string
  sourceId: string
  status: 'active' | 'inactive' | 'error'
  lastUpdated?: string
  itemCount?: number
}

export interface Source {
  id: string
  name: string
  description?: string
  status: 'active' | 'inactive'
  feedCount?: number
  createdAt?: string
}

export interface ListResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface ApiError {
  message: string
  code?: string
  status?: number
}
