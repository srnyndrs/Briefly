import React, { useState } from 'react'
import { Feed } from '@/types'
import './FeedForm.css'

interface FeedFormProps {
  onSubmit: (data: Omit<Feed, 'id'>) => void
  isLoading?: boolean
  initialData?: Partial<Omit<Feed, 'id'>>
}

export const FeedForm: React.FC<FeedFormProps> = ({ onSubmit, isLoading = false, initialData }) => {
  const [formData, setFormData] = useState<Omit<Feed, 'id'>>(
    (initialData as Omit<Feed, 'id'>) || {
      title: '',
      description: '',
      url: '',
      sourceId: '',
      status: 'active',
    }
  )

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
    setFormData({
      title: '',
      description: '',
      url: '',
      sourceId: '',
      status: 'active',
    })
  }

  return (
    <form onSubmit={handleSubmit} className="feed-form">
      <div className="form-group">
        <label htmlFor="title">Title *</label>
        <input
          id="title"
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          placeholder="Enter feed title"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="url">Feed URL *</label>
        <input
          id="url"
          type="url"
          name="url"
          value={formData.url}
          onChange={handleChange}
          placeholder="https://example.com/feed"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          name="description"
          value={formData.description || ''}
          onChange={handleChange}
          placeholder="Enter feed description"
          rows={3}
        ></textarea>
      </div>

      <div className="form-group">
        <label htmlFor="sourceId">Source ID *</label>
        <input
          id="sourceId"
          type="text"
          name="sourceId"
          value={formData.sourceId}
          onChange={handleChange}
          placeholder="Select or enter source ID"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="status">Status</label>
        <select name="status" value={formData.status} onChange={handleChange}>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="error">Error</option>
        </select>
      </div>

      <button type="submit" disabled={isLoading} className="btn-primary">
        {isLoading ? 'Saving...' : 'Save Feed'}
      </button>
    </form>
  )
}
