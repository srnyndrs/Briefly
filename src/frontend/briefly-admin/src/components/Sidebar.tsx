import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAdminStore } from '@/stores/admin'
import './Sidebar.css'

export const Sidebar: React.FC = () => {
  const { sidebarOpen, toggleSidebar } = useAdminStore()

  return (
    <>
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>📰 Briefly</h2>
          <button className="toggle-btn" onClick={toggleSidebar}>
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
            <span className="icon">📊</span>
            {sidebarOpen && <span>Dashboard</span>}
          </NavLink>
          <NavLink to="/feeds" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="icon">📑</span>
            {sidebarOpen && <span>Feeds</span>}
          </NavLink>
          <NavLink to="/sources" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="icon">📚</span>
            {sidebarOpen && <span>Sources</span>}
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <button className="settings-btn">
            <span className="icon">⚙️</span>
            {sidebarOpen && <span>Settings</span>}
          </button>
        </div>
      </aside>

      {sidebarOpen && <div className="sidebar-overlay" onClick={toggleSidebar}></div>}
    </>
  )
}
