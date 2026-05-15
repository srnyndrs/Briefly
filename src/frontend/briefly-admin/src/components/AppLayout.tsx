import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

const linkClassName = ({ isActive }: { isActive: boolean }): string =>
  [
    'rounded-full px-4 py-2 text-sm font-semibold transition-colors',
    isActive ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-200',
  ].join(' ');

export const AppLayout = (): React.JSX.Element => {
  return (
    <div className="mx-auto min-h-screen w-full max-w-7xl px-4 pb-10 pt-6 sm:px-6 lg:px-8">
      <header className="mb-8 rounded-3xl border border-slate-200/80 bg-white/80 p-5 backdrop-blur-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Briefly</p>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Admin Console</h1>
          </div>
          <nav className="flex items-center gap-2">
            <NavLink to="/articles" className={linkClassName}>
              Articles
            </NavLink>
            <NavLink to="/feeds" className={linkClassName}>
              Feeds
            </NavLink>
          </nav>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
};
