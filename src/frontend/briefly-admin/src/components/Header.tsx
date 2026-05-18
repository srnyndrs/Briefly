import React from 'react'
import './Header.css'

interface HeaderProps {
  title: string
  subtitle?: string
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-text">
          <h1>{title}</h1>
          {subtitle && <p className="subtitle">{subtitle}</p>}
        </div>
        <div className="header-actions">
          <button className="btn-secondary">🔔 Notifications</button>
          <div className="user-avatar">👤</div>
        </div>
      </div>
    </header>
  )
}
