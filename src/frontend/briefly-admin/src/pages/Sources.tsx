import React, { useState } from 'react'
import { useSources, useCreateSource, useUpdateSource, useDeleteSource } from '@/hooks/useApi'
import { Header } from '@/components/Header'
import { SourceForm } from '@/components/SourceForm'
import { Source } from '@/types'

export const Sources: React.FC = () => {
  const [page] = useState(1)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingSource, setEditingSource] = useState<Source | null>(null)

  const { data, isLoading, error } = useSources(page)
  const createSource = useCreateSource()
  const updateSource = useUpdateSource()
  const deleteSource = useDeleteSource()

  const handleSubmit = async (formData: Omit<Source, 'id'>) => {
    try {
      if (editingSource) {
        await updateSource.mutateAsync({ id: editingSource.id, data: formData })
      } else {
        await createSource.mutateAsync(formData)
      }
      setIsFormOpen(false)
      setEditingSource(null)
    } catch (err) {
      console.error('Failed to save source:', err)
    }
  }

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this source?')) {
      try {
        await deleteSource.mutateAsync(id)
      } catch (err) {
        console.error('Failed to delete source:', err)
      }
    }
  }

  const handleEdit = (source: Source) => {
    setEditingSource(source)
    setIsFormOpen(true)
  }

  return (
    <div>
      <Header title="Sources" subtitle="Manage your content sources" />
      <div className="container">
        <div className="page-header">
          <button
            onClick={() => {
              setEditingSource(null)
              setIsFormOpen(!isFormOpen)
            }}
            className="btn-create"
          >
            ➕ Add New Source
          </button>
        </div>

        {isFormOpen && (
          <div className="form-container">
            <div className="form-wrapper">
              <button className="close-btn" onClick={() => setIsFormOpen(false)}>
                ✕
              </button>
              <h3>{editingSource ? 'Edit Source' : 'Create New Source'}</h3>
              <SourceForm
                onSubmit={handleSubmit}
                isLoading={createSource.isPending || updateSource.isPending}
                initialData={editingSource || undefined}
              />
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="loading">Loading sources...</div>
        ) : error ? (
          <div className="error">Failed to load sources</div>
        ) : (
          <div className="sources-list">
            {data?.items?.length === 0 ? (
              <div className="empty-state">
                <p>📭 No sources yet. Create one to get started!</p>
              </div>
            ) : (
              data?.items?.map((source) => (
                <div key={source.id} className="source-card">
                  <div className="source-header">
                    <h3>{source.name}</h3>
                    <span className={`status-badge status-${source.status}`}>
                      {source.status}
                    </span>
                  </div>
                  <p className="source-description">{source.description}</p>
                  <div className="source-footer">
                    <div className="source-meta">
                      <span>📑 {source.feedCount || 0} feeds</span>
                    </div>
                    <div className="source-actions">
                      <button onClick={() => handleEdit(source)} className="btn-small">
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => handleDelete(source.id)}
                        className="btn-small btn-danger"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <style>{`
        .container {
          padding: 30px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .page-header {
          margin-bottom: 30px;
        }

        .btn-create {
          padding: 12px 24px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-create:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .form-container {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .form-wrapper {
          background: white;
          border-radius: 12px;
          padding: 30px;
          max-width: 600px;
          width: 90%;
          position: relative;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        }

        .form-wrapper h3 {
          margin: 0 0 20px 0;
          font-size: 20px;
        }

        .close-btn {
          position: absolute;
          top: 15px;
          right: 15px;
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #999;
        }

        .sources-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 20px;
        }

        .source-card {
          background: white;
          border-radius: 12px;
          border: 1px solid #e0e0e0;
          padding: 20px;
          transition: all 0.3s;
        }

        .source-card:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
          border-color: #667eea;
        }

        .source-header {
          display: flex;
          justify-content: space-between;
          align-items: start;
          margin-bottom: 12px;
        }

        .source-header h3 {
          margin: 0;
          font-size: 16px;
          color: #1a1a1a;
        }

        .status-badge {
          padding: 4px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
        }

        .status-active {
          background: #d4edda;
          color: #155724;
        }

        .status-inactive {
          background: #e2e3e5;
          color: #383d41;
        }

        .source-description {
          margin: 8px 0;
          font-size: 14px;
          color: #666;
          line-height: 1.4;
        }

        .source-footer {
          border-top: 1px solid #f0f0f0;
          padding-top: 12px;
        }

        .source-meta {
          display: flex;
          gap: 16px;
          margin-bottom: 12px;
          font-size: 13px;
          color: #999;
        }

        .source-actions {
          display: flex;
          gap: 8px;
        }

        .btn-small {
          padding: 6px 12px;
          background: #f0f0f0;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-small:hover {
          background: #e0e0e0;
          border-color: #999;
        }

        .btn-danger:hover {
          background: #f8d7da;
          border-color: #721c24;
          color: #721c24;
        }

        .loading,
        .error {
          text-align: center;
          padding: 40px;
          color: #666;
        }

        .error {
          color: #dc3545;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #999;
        }
      `}</style>
    </div>
  )
}
