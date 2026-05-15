import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { ArticleDetailPage } from './pages/ArticleDetailPage';
import { ArticlesPage } from './pages/ArticlesPage';
import { FeedsPage } from './pages/FeedsPage';
import { NotFoundPage } from './pages/NotFoundPage';

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate replace to="/articles" />} />
        <Route path="/articles" element={<ArticlesPage />} />
        <Route path="/articles/:id" element={<ArticleDetailPage />} />
        <Route path="/feeds" element={<FeedsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
