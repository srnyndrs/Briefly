import { create } from 'zustand'
import { Feed, Source } from '@/types'

interface AdminStore {
  // UI State
  sidebarOpen: boolean
  toggleSidebar: () => void
  
  // Active selections
  activeFeedId: string | null
  activeSourceId: string | null
  setActiveFeedId: (id: string | null) => void
  setActiveSourceId: (id: string | null) => void
  
  // Modal states
  isAddFeedModalOpen: boolean
  isAddSourceModalOpen: boolean
  isEditModalOpen: boolean
  openAddFeedModal: () => void
  openAddSourceModal: () => void
  openEditModal: () => void
  closeModals: () => void
  
  // Cached data
  feeds: Feed[]
  sources: Source[]
  setFeeds: (feeds: Feed[]) => void
  setSources: (sources: Source[]) => void
}

export const useAdminStore = create<AdminStore>((set) => ({
  // UI State
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  // Active selections
  activeFeedId: null,
  activeSourceId: null,
  setActiveFeedId: (id) => set({ activeFeedId: id }),
  setActiveSourceId: (id) => set({ activeSourceId: id }),
  
  // Modal states
  isAddFeedModalOpen: false,
  isAddSourceModalOpen: false,
  isEditModalOpen: false,
  openAddFeedModal: () => set({ isAddFeedModalOpen: true }),
  openAddSourceModal: () => set({ isAddSourceModalOpen: true }),
  openEditModal: () => set({ isEditModalOpen: true }),
  closeModals: () =>
    set({
      isAddFeedModalOpen: false,
      isAddSourceModalOpen: false,
      isEditModalOpen: false,
    }),
  
  // Cached data
  feeds: [],
  sources: [],
  setFeeds: (feeds) => set({ feeds }),
  setSources: (sources) => set({ sources }),
}))
