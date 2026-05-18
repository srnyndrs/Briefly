import React, { useState } from 'react'
import { Source } from '@/types'
import './SourceForm.css'

interface SourceFormProps {
  onSubmit: (data: Omit<Source, 'id'>) => void
  isLoading?: boolean
  initialData?: Partial<Omit<Source, 'id'>>
}

export const SourceForm: React.FC<SourceFormProps> = ({ onSubmit, isLoading = false, initialData }) => {
  const [formData, setFormData] = useState<Omit<Source, 'id'>>(
    (initialData as Omit<Source, 'id'>) || {
      name: '',
      description: '',
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
      name: '',
      description: '',
      status: 'active',
    })
  }

  return (
    <form onSubmit={handleSubmit} className="source-form">
      <div className="form-group">
        <label htmlFor="name">Name *</label>
        <input
          id="name"
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="Enter source name"
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
          placeholder="Enter source description"
          rows={3}
        ></textarea>
      </div>

      <div className="form-group">
        <label htmlFor="status">Status</label>
        <select name="status" value={formData.status} onChange={handleChange}>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      <button type="submit" disabled={isLoading} className="btn-primary">
        {isLoading ? 'Saving...' : 'Save Source'}
      </button>
    </form>
  )
}
