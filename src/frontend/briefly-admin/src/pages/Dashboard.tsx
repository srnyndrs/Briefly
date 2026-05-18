import React from 'react'
import { Header } from '@/components/Header'

export const Dashboard: React.FC = () => {
  return (
    <div>
      <Header title="Dashboard" subtitle="Welcome to Briefly Admin Portal" />
      <div className="container">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📑</div>
            <div className="stat-content">
              <h3>Active Feeds</h3>
              <p className="stat-number">24</p>
              <span className="stat-meta">+3 this week</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📚</div>
            <div className="stat-content">
              <h3>Sources</h3>
              <p className="stat-number">8</p>
              <span className="stat-meta">All active</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <h3>Feed Errors</h3>
              <p className="stat-number">2</p>
              <span className="stat-meta">Action required</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⏱️</div>
            <div className="stat-content">
              <h3>Last Update</h3>
              <p className="stat-number">2m</p>
              <span className="stat-meta">ago</span>
            </div>
          </div>
        </div>

        <div className="recent-activity">
          <h2>Recent Activity</h2>
          <div className="activity-list">
            <div className="activity-item">
              <div className="activity-icon">✅</div>
              <div className="activity-content">
                <p className="activity-title">Feed Updated</p>
                <p className="activity-meta">TechNews - Updated 5 minutes ago</p>
              </div>
              <span className="activity-time">5m ago</span>
            </div>
            <div className="activity-item">
              <div className="activity-icon">⚠️</div>
              <div className="activity-content">
                <p className="activity-title">Feed Error</p>
                <p className="activity-meta">DevBlog - Connection timeout</p>
              </div>
              <span className="activity-time">12m ago</span>
            </div>
            <div className="activity-item">
              <div className="activity-icon">➕</div>
              <div className="activity-content">
                <p className="activity-title">New Source Added</p>
                <p className="activity-meta">Engineering Blogs</p>
              </div>
              <span className="activity-time">1h ago</span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .container {
          padding: 30px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 20px;
          margin-bottom: 40px;
        }

        .stat-card {
          background: white;
          padding: 24px;
          border-radius: 12px;
          border: 1px solid #e0e0e0;
          display: flex;
          gap: 16px;
          transition: all 0.3s;
        }

        .stat-card:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
          transform: translateY(-2px);
        }

        .stat-icon {
          font-size: 32px;
          min-width: 50px;
          height: 50px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-content {
          flex: 1;
        }

        .stat-content h3 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #666;
          font-weight: 600;
        }

        .stat-number {
          margin: 0;
          font-size: 28px;
          font-weight: 700;
          color: #1a1a1a;
        }

        .stat-meta {
          font-size: 12px;
          color: #999;
        }

        .recent-activity {
          background: white;
          padding: 24px;
          border-radius: 12px;
          border: 1px solid #e0e0e0;
        }

        .recent-activity h2 {
          margin: 0 0 20px 0;
          font-size: 18px;
        }

        .activity-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .activity-item {
          display: flex;
          gap: 12px;
          padding: 12px;
          background: #fafafa;
          border-radius: 8px;
          align-items: center;
        }

        .activity-icon {
          font-size: 20px;
          min-width: 28px;
          display: flex;
          align-items: center;
        }

        .activity-content {
          flex: 1;
        }

        .activity-title {
          margin: 0;
          font-weight: 600;
          font-size: 14px;
        }

        .activity-meta {
          margin: 4px 0 0 0;
          font-size: 12px;
          color: #666;
        }

        .activity-time {
          font-size: 12px;
          color: #999;
          white-space: nowrap;
        }
      `}</style>
    </div>
  )
}
